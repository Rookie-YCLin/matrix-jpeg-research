"""Predeclared paper-derived QIM experiment; see docs/PAPER_LOW_QF_PLAN.md."""
from __future__ import annotations

import argparse
import copy
import csv
import json
import platform
from importlib.metadata import distribution, version
from pathlib import Path
from types import MethodType
from urllib.request import urlopen

import numpy as np
import cv2
from cv2 import dct, idct
from PIL import Image, features
from pywt import idwt2

from experiments import ori_qf_scan as fixed
from experiments.svd_qim_sweep import configured_instance
from blind_watermark.bwm_core import one_dim_kmeans, random_strategy1


def centered_quantize(value, period, bit, minimum=0.0):
    target = period * (np.floor(value / period + 0.5) + (2 * int(bit) - 1) / 4)
    return target + max(0, np.ceil((minimum - target) / period)) * period


def centered_decode(value, period):
    # Distance to the two periodic cosets, with ties assigned to zero.
    distances = [abs((value / period - (2*b-1)/4 + 0.5) % 1 - 0.5) for b in (0, 1)]
    return int(distances[1] < distances[0])


def nearest_zero_quantize(value, period, bit, minimum=0.0):
    offset = int(bit) / 2
    index = max(np.floor(value / period - offset + 0.5), np.ceil(minimum / period - offset))
    return period * (index + offset)


def nearest_zero_decode(value, period):
    distances = [abs((value / period - b/2 + 0.5) % 1 - 0.5) for b in (0, 1)]
    return int(distances[1] < distances[0])


def paper_embed(self, args):
    block, shuffler, i = args
    bit = self.wm_bit[i % self.wm_size]
    u, s, v = np.linalg.svd(dct(block).flatten()[shuffler].reshape(self.block_shape))
    s[1] = (s[1] // self.d2 + 0.25 + 0.5 * bit) * self.d2
    period = max(float(s[1]), self.d1) if self.paper_ratio else self.d1
    quantize = nearest_zero_quantize if self.paper_zero else centered_quantize
    s[0] = quantize(s[0], period, bit, minimum=s[1])
    flat = (u @ np.diag(s) @ v).flatten()
    flat[shuffler] = flat.copy()
    return idct(flat.reshape(self.block_shape))


def paper_extract(self, args):
    block, shuffler = args
    s = np.linalg.svd(dct(block).flatten()[shuffler].reshape(self.block_shape), compute_uv=False)
    period = max(float(s[1]), self.d1) if self.paper_ratio else self.d1
    first = (nearest_zero_decode if self.paper_zero else centered_decode)(s[0], period)
    second = int(s[1] % self.d2 > self.d2 / 2)
    return (3 * first + second) / 4


# One selected cycle out of every 32 carries each payload bit.  The pattern is
# deterministic from the public block index and therefore available blind at
# extraction, but is independent of the JPEG QF and of the unknown bit value.
SPARSE_CYCLE_PERIOD = 32
ADAPTIVE_REPLICAS_PER_CHANNEL = 7


def sparse_selected(i, wm_size, cycle_period=SPARSE_CYCLE_PERIOD):
    return (i // wm_size) % cycle_period == 0


def sparse_embed(self, args):
    block, shuffler, i = args
    if not sparse_selected(i, self.wm_size, self.sparse_cycle_period):
        return block.copy()
    bit = self.wm_bit[i % self.wm_size]
    u, s, v = np.linalg.svd(dct(block).flatten()[shuffler].reshape(self.block_shape))
    s[0] = (s[0] // self.d1 + 0.25 + 0.5 * bit) * self.d1
    flat = (u @ np.diag(s) @ v).flatten()
    flat[shuffler] = flat.copy()
    return idct(flat.reshape(self.block_shape))


def top_energy_indices(core, channel, replicas):
    """Pick the largest sigma_1 values separately for every repeated payload bit."""
    scores = np.empty(core.block_num, dtype=np.float64)
    for i, index in enumerate(core.block_index):
        block = core.ca_block[channel][index]
        shuffled = dct(block).flatten()[core.idx_shuffle[i]].reshape(core.block_shape)
        scores[i] = np.linalg.svd(shuffled, compute_uv=False)[0]
    selected = []
    for bit_index in range(core.wm_size):
        candidates = np.arange(bit_index, core.block_num, core.wm_size)
        order = np.argsort(-scores[candidates], kind="stable")
        selected.extend(candidates[order[:replicas]].tolist())
    return selected


def adaptive_top_energy_embed(self):
    self.init_block_index()
    embedded_ca = copy.deepcopy(self.ca)
    embedded_yuv = [np.array([])] * 3
    self.idx_shuffle = random_strategy1(self.password_img, self.block_num, 16)
    for channel in range(3):
        selected = set(top_energy_indices(self, channel, self.adaptive_replicas))
        updated = []
        for i, index in enumerate(self.block_index):
            block = self.ca_block[channel][index]
            if i not in selected:
                updated.append(block.copy())
                continue
            bit = self.wm_bit[i % self.wm_size]
            shuffled = dct(block).flatten()[self.idx_shuffle[i]].reshape(self.block_shape)
            u, s, v = np.linalg.svd(shuffled)
            s[0] = (s[0] // self.d1 + 0.25 + 0.5 * bit) * self.d1
            flat = (u @ np.diag(s) @ v).flatten()
            flat[self.idx_shuffle[i]] = flat.copy()
            updated.append(idct(flat.reshape(self.block_shape)))
        for i, index in enumerate(self.block_index):
            self.ca_block[channel][index] = updated[i]
        self.ca_part[channel] = np.concatenate(np.concatenate(self.ca_block[channel], 1), 1)
        embedded_ca[channel][:self.part_shape[0], :self.part_shape[1]] = self.ca_part[channel]
        embedded_yuv[channel] = idwt2((embedded_ca[channel], self.hvd[channel]), "haar")
    result_yuv = np.stack(embedded_yuv, axis=2)[:self.img_shape[0], :self.img_shape[1]]
    result = np.clip(cv2.cvtColor(result_yuv, cv2.COLOR_YUV2BGR), 0, 255)
    if self.alpha is not None:
        result = cv2.merge([result.astype(np.uint8), self.alpha])
    return result


def adaptive_top_energy_extract_with_kmeans(self, img, wm_shape):
    self.wm_size = np.array(wm_shape).prod()
    self.read_img_arr(img=img)
    self.init_block_index()
    self.idx_shuffle = random_strategy1(self.password_img, self.block_num, 16)
    votes = [[] for _ in range(self.wm_size)]
    for channel in range(3):
        for i in top_energy_indices(self, channel, self.adaptive_replicas):
            index = self.block_index[i]
            shuffled = dct(self.ca_block[channel][index]).flatten()[self.idx_shuffle[i]].reshape(self.block_shape)
            s = np.linalg.svd(shuffled, compute_uv=False)
            votes[i % self.wm_size].append(float(s[0] % self.d1 > self.d1 / 2))
    if any(not bit_votes for bit_votes in votes):
        raise RuntimeError("Adaptive selector selected no replicas for a payload bit")
    return one_dim_kmeans(np.array([np.mean(bit_votes) for bit_votes in votes]))


def sparse_extract_with_kmeans(self, img, wm_shape):
    self.wm_size = np.array(wm_shape).prod()
    self.read_img_arr(img=img)
    self.init_block_index()
    self.idx_shuffle = random_strategy1(self.password_img, self.block_num, 16)
    values = [[] for _ in range(self.wm_size)]
    for channel in range(3):
        selected = [
            i for i in range(self.block_num)
            if sparse_selected(i, self.wm_size, self.sparse_cycle_period)
        ]
        blocks = [
            (self.ca_block[channel][self.block_index[i]], self.idx_shuffle[i])
            for i in selected
        ]
        decoded = self.pool.map(self.block_get_wm_slow, blocks)
        for i, bit in zip(selected, decoded):
            values[i % self.wm_size].append(float(bit))
    if any(not x for x in values):
        raise RuntimeError("Sparse extractor selected no replicas for a payload bit")
    return one_dim_kmeans(np.array([np.mean(x) for x in values]))


def instance(variant):
    if variant not in ('upstream', 'g6', 'paper_centered90', 'paper_ratio_floor90', 'paper_nearest_zero90', 'matrix_margin720', 'sparse_margin720', 'adaptive_top_energy720'):
        raise ValueError(variant)
    wm = configured_instance(36 if variant == 'upstream' else (720 if variant in ('matrix_margin720', 'sparse_margin720', 'adaptive_top_energy720') else 90), 20)
    if variant == 'adaptive_top_energy720':
        core = wm.bwm_core
        core.adaptive_replicas = ADAPTIVE_REPLICAS_PER_CHANNEL
        core.embed = MethodType(adaptive_top_energy_embed, core)
        core.extract_with_kmeans = MethodType(adaptive_top_energy_extract_with_kmeans, core)
        return wm
    if variant == 'sparse_margin720':
        core = wm.bwm_core
        core.sparse_cycle_period = 32
        core.block_add_wm_slow = MethodType(sparse_embed, core)
        core.extract_with_kmeans = MethodType(sparse_extract_with_kmeans, core)
        return wm
    if variant.startswith('paper_'):
        core = wm.bwm_core
        core.paper_ratio = variant == 'paper_ratio_floor90'
        core.paper_zero = variant == 'paper_nearest_zero90'
        core.block_add_wm_slow = MethodType(paper_embed, core)
        core.block_get_wm_slow = MethodType(paper_extract, core)
    return wm


def decode(rgb, variant):
    bits = np.asarray(instance(variant).extract(embed_img=fixed.to_bgr(rgb), wm_shape=32, mode='bit'))
    if bits.shape != (32,) or not np.isin(bits, [0, 1]).all():
        raise ValueError('Invalid decoder output')
    return ''.join(str(int(b)) for b in bits)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    parser.add_argument('--variants', nargs='+', default=['upstream', 'g6', 'paper_centered90', 'paper_ratio_floor90'])
    parser.add_argument('--qualities', nargs='+', type=int, default=[5, 10, 15, 20])
    args = parser.parse_args()
    provenance = json.loads(distribution('blind_watermark').read_text('direct_url.json'))
    if provenance.get('vcs_info', {}).get('commit_id') != fixed.UPSTREAM_COMMIT:
        raise RuntimeError('Wrong upstream commit')
    out = args.output_dir
    out.mkdir(parents=True, exist_ok=False)
    source = out / 'ori_img.jpeg'
    with urlopen(fixed.SOURCE_URL, timeout=60) as response:
        source.write_bytes(response.read())
    if fixed.git_blob_sha(source.read_bytes()) != fixed.SOURCE_BLOB_SHA:
        raise RuntimeError('Wrong source image')
    rgb = fixed.read_rgb(source)
    rows = []
    for variant in args.variants:
        marked = out / f'{variant}_marked.png'
        encoder = instance(variant)
        encoder.read_img(img=fixed.to_bgr(rgb))
        encoder.read_wm([int(b) for b in fixed.PAYLOAD], mode='bit')
        encoder.embed(filename=str(marked))
        for qf in [None, *args.qualities]:
            attacked = marked if qf is None else out / f'{variant}_qf{qf:02d}.jpg'
            if qf is not None:
                with Image.open(marked) as image:
                    image.save(attacked, format='JPEG', quality=qf, **fixed.JPEG)
            pixels = fixed.read_rgb(attacked)
            bits = decode(pixels, variant)
            wrong = [i+1 for i,(a,b) in enumerate(zip(fixed.PAYLOAD,bits)) if a != b]
            mse = float(np.mean((rgb.astype(np.float64)-pixels.astype(np.float64))**2))
            row = dict(variant=variant, qf='PNG' if qf is None else qf, errors=len(wrong), total_bits=32,
                       ber=len(wrong)/32, expected_bits=fixed.PAYLOAD, extracted_bits=bits,
                       positions_1based=json.dumps(wrong), mse=mse, psnr_db=10*np.log10(255**2/mse),
                       filename=attacked.name, sha256=fixed.sha256_file(attacked))
            rows.append(row)
            print(f'{variant} QF={row["qf"]}: {len(wrong)}/32', flush=True)
            with (out/'results.csv').open('w',newline='',encoding='utf-8') as stream:
                writer = csv.DictWriter(stream, fieldnames=list(row), lineterminator='\n')
                writer.writeheader()
                writer.writerows(rows)
    manifest = dict(upstream_provenance=provenance, source=str(source), source_sha256=fixed.sha256_file(source),
                    payload=fixed.PAYLOAD, keys=fixed.KEYS, variants=args.variants, qualities=args.qualities,
                    jpeg=fixed.JPEG, python=platform.python_version(), pillow_jpeg=features.version('jpg'),
                    packages={k:version(k) for k in ('numpy','Pillow','opencv-python','PyWavelets','blind_watermark')},
                    code_sha256=fixed.sha256_file(Path(__file__)),
                    files_sha256={p.name:fixed.sha256_file(p) for p in sorted(out.iterdir())})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()

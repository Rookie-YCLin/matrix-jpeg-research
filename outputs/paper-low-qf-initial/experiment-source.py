"""Predeclared paper-derived QIM experiment; see docs/PAPER_LOW_QF_PLAN.md."""
from __future__ import annotations

import argparse
import csv
import json
import platform
from importlib.metadata import distribution, version
from pathlib import Path
from types import MethodType
from urllib.request import urlopen

import numpy as np
from cv2 import dct, idct
from PIL import Image, features

from experiments import ori_qf_scan as fixed
from experiments.svd_qim_sweep import configured_instance


def centered_quantize(value, period, bit, minimum=0.0):
    target = period * (np.floor(value / period + 0.5) + (2 * int(bit) - 1) / 4)
    return target + max(0, np.ceil((minimum - target) / period)) * period


def centered_decode(value, period):
    # Distance to the two periodic cosets, with ties assigned to zero.
    distances = [abs((value / period - (2*b-1)/4 + 0.5) % 1 - 0.5) for b in (0, 1)]
    return int(distances[1] < distances[0])


def paper_embed(self, args):
    block, shuffler, i = args
    bit = self.wm_bit[i % self.wm_size]
    u, s, v = np.linalg.svd(dct(block).flatten()[shuffler].reshape(self.block_shape))
    s[1] = (s[1] // self.d2 + 0.25 + 0.5 * bit) * self.d2
    period = max(float(s[1]), self.d1) if self.paper_ratio else self.d1
    s[0] = centered_quantize(s[0], period, bit, minimum=s[1])
    flat = (u @ np.diag(s) @ v).flatten()
    flat[shuffler] = flat.copy()
    return idct(flat.reshape(self.block_shape))


def paper_extract(self, args):
    block, shuffler = args
    s = np.linalg.svd(dct(block).flatten()[shuffler].reshape(self.block_shape), compute_uv=False)
    period = max(float(s[1]), self.d1) if self.paper_ratio else self.d1
    first = centered_decode(s[0], period)
    second = int(s[1] % self.d2 > self.d2 / 2)
    return (3 * first + second) / 4


def instance(variant):
    if variant not in ('upstream', 'g6', 'paper_centered90', 'paper_ratio_floor90'):
        raise ValueError(variant)
    wm = configured_instance(36 if variant == 'upstream' else 90, 20)
    if variant.startswith('paper_'):
        core = wm.bwm_core
        core.paper_ratio = variant == 'paper_ratio_floor90'
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

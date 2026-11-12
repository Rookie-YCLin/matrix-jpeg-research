"""Offline diagnostics only: truth groups never feed the blind decoder."""
import argparse
import json
from pathlib import Path

import numpy as np
from cv2 import dct
from blind_watermark.bwm_core import random_strategy1

from experiments.paper_low_qf import instance
from experiments import ori_qf_scan as fixed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input-dir', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    encoder = instance('g6')
    encoder.read_wm([int(x) for x in fixed.PAYLOAD], mode='bit')
    truth = encoder.bwm_core.wm_bit
    values = {}
    names = ['g6_marked.png', 'g6_qf05.jpg', 'g6_qf10.jpg']
    for name in names:
        core = instance('g6').bwm_core
        core.wm_size = 32
        core.read_img_arr(fixed.to_bgr(fixed.read_rgb(args.input_dir/name)))
        core.init_block_index()
        sh = random_strategy1(1, core.block_num, 16)
        blocks = np.array([[dct(core.ca_block[ch][ij]).ravel()[sh[i]].reshape(4,4)
                            for i,ij in enumerate(core.block_index)] for ch in range(3)])
        values[name] = np.linalg.svd(blocks, compute_uv=False)
    result = {}
    for name, s in values.items():
        rows = []
        for ch in range(3):
            for bit in [0,1]:
                mask = truth[np.arange(core.block_num)%32] == bit
                z = s[ch,mask,0]
                delta = z-values['g6_marked.png'][ch,mask,0]
                rows.append(dict(channel=ch, bit=bit, count=int(mask.sum()),
                    s1_median=float(np.median(z)), s2_median=float(np.median(s[ch,mask,1])),
                    s1_mod90_mean=float(np.mean(z%90)), first_one_rate=float(np.mean(z%90>45)),
                    delta_quantiles=np.quantile(delta,[0,.1,.5,.9,1]).tolist()))
        result[name] = rows
    result['provenance'] = dict(code_sha256=fixed.sha256_file(Path(__file__)),
        input_sha256={n:fixed.sha256_file(args.input_dir/n) for n in names},
        meaning='Offline truth-conditioned diagnostics; no decoder adaptation')
    args.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')


if __name__ == '__main__':
    main()

# SVD-QIM five edge-case experiment — 2026-11-14

Pinned experiment: https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/43596940607

Source: upstream `ori_img.jpeg` with frozen blob, original 32-bit payload, same passwords, `mode=common`, `fast_mode=False`, same Pillow JPEG RGB 4:4:4 conditions. Unchanged upstream implementation; `d1=0` is invalid because the first singular value is always quantized, so (0,20) and (0,720) are recorded as invalid rather than fabricated BER results.

| QF | (36,0) BER | (720,720) BER | (720,0) BER |
|---|---:|---:|---:|
| PNG | 0.000% (0/32) | 0.000% (0/32) | 0.000% (0/32) |
| 5 | 34.375% (11/32) | 0.000% (0/32) | 0.000% (0/32) |
| 10 | 3.125% (1/32) | 0.000% (0/32) | 0.000% (0/32) |
| 15 | 100.000% (32/32) | 0.000% (0/32) | 0.000% (0/32) |
| 20 | 100.000% (32/32) | 0.000% (0/32) | 0.000% (0/32) |
| 25 | 0.000% (0/32) | 0.000% (0/32) | 0.000% (0/32) |
| 50 | 0.000% (0/32) | 0.000% (0/32) | 0.000% (0/32) |
| 95 | 0.000% (0/32) | 0.000% (0/32) | 0.000% (0/32) |

Uncompressed PNG PSNR: (36,0) 39.886 dB; (720,720) 12.310 dB; (720,0) 15.566 dB.

This study uses one image and one payload, not a population-level performance estimate. The extreme-720 settings produce severe visible distortion even though the sampled QFs decode without bit errors.

# Fixed d1=36, extreme d2=720 experiment

GitHub Actions run: https://github.com/Rookie-YCLin/matrix-jpeg-research/actions/runs/43596202831

Source and configuration follow `experiments/ori_qf_scan.py`: single pinned upstream image; 32-bit original payload, password_img=1, password_wm=1; mode=common; fast_mode=False; JPEG Pillow RGB 4:4:4. The upstream implementation is pinned to commit `322c90dc02d45644692095b34d3a6b735b6edbd8`.

Primary experiment changes only d2 from 20 to 720 while holding d1=36.

| QF | baseline errors (d2=20) | experimental errors (d2=720) | baseline PSNR dB | experimental PSNR dB |
|---|---:|---:|---:|---:|
| PNG | 0/32 | 0/32 | 38.401 | 12.614 |
| 5 | 12/32 | 0/32 | 24.737 | 12.974 |
| 10 | 1/32 | 7/32 | 27.890 | 13.155 |
| 15 | 32/32 | 2/32 | 29.225 | 13.126 |
| 20 | 32/32 | 1/32 | 29.967 | 13.082 |
| 25 | 0/32 | 0/32 | 30.933 | 12.933 |
| 50 | 0/32 | 0/32 | 33.085 | 12.786 |
| 95 | 0/32 | 0/32 | 38.087 | 12.640 |

The result is exploratory (one image, one 32-bit payload). The marked PNG PSNR declines from 38.401 to 12.614 dB. The JPEG QF=5 BER is 12/32 vs 0/32; QF=10 1/32 vs 7/32; QF=15 32/32 vs 2/32; QF=20 32/32 vs 1/32. Strong distortion means d2=720 is not an acceptable high-fidelity default. Singular-value reorder rates were not measured in this run.

The raw results are in [results.csv](results.csv); the run artifact also contains PNG/JPEG images.

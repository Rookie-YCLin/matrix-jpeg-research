# Content-adaptive top-energy SVD-QIM

Objective order is fixed: first obtain BER=0 at QF5, then maximize PSNR without changing the payload, keys, JPEG pipeline, or blindness condition. This candidate uses no truth bits, source image, or JPEG quality at extraction.

For each colour channel and each repeated payload coordinate, form the candidate block set `i = r mod 32`. Compute the first singular value `sigma_1` of every candidate's shuffled DCT block. Select the seven largest `sigma_1` blocks, embed only there with first-singular-value QIM period 720, and leave all other blocks unchanged. The blind extractor recomputes the same top-seven ranking after attack and averages only those votes.

The number seven is fixed before this test: it matches the approximate replicas-per-channel obtained by the failed 1/64 fixed schedule, whose PSNR was high but QF5 BER was not. The selection changes positions, not the number of strong replicas or d1. The fixed schedule failed QF5 at 25/32; no other replica count is tried here.

Matrix rationale: the selected subspace consists of blocks with high dominant singular energy. For a fixed block basis, embedding cost remains `||A'-A||_F^2 = sum_j (sigma'_j-sigma_j)^2`; non-selected blocks cost zero. Selecting high-energy blocks is a robustness hypothesis, not a theorem: their dominant mode may have more stable ordering under JPEG, and their local perturbation may be less visually conspicuous relative to host structure. Both claims require measured BER and PSNR.

Pass: PNG and QF5/10/15/20 are all 0/32, then validate QF5..95 step 5. Do not claim all-image generalization from the primary image. External images are a separately labelled validation only.

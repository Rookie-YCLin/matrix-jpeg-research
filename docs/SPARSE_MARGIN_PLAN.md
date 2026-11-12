# Sparse-margin SVD-QIM: pre-registered design

The all-block d1=720 candidate eliminates QF5 errors but has PNG PSNR 15.56 dB. This candidate keeps its per-selected-block first-singular-value QIM period at 720 but embeds only in cycle numbers congruent to zero modulo 32. A payload bit occurs once per 32-block cycle, so every payload coordinate has the same number of selected replicas. The selection depends only on the public block index, the fixed 32-bit length and the fixed key's shuffle pipeline; it does not observe JPEG quality, source image, or true bits at decoding.

Embedding changes only the selected block's first singular value. The extractor computes the same selected set and K-means clusters only their decoded votes. Unselected blocks are not treated as zero votes. d2 remains configured at 20 but is not modified by this candidate.

For fixed singular bases, selected-block embedding energy is the sum of squared singular-value changes. Since unselected blocks have zero perturbation, the summed local Frobenius energy is reduced relative to embedding all blocks at the same period. This does not prove RGB PSNR, nor does the singular-value perturbation bound prove JPEG BER; both are measured.

Pass requirements: PNG and QF5/10/15/20 must be 0/32, QF5 must improve on G6 32/32, then validate existing QF5..95 grid. Record PSNR without treating it as a BER surrogate. No period sweep or decoder QF adaptation is permitted.

# GPU_RUN3 — search budget comparison

Base run: `gpu_run3_full_20260817`  
Extended run: `gpu_run3_extended_1800s_groupB_20260818`

Paired by system and seed: identical systems, seeds and simulation conditions;
only the MCTS budget differs. The extended run also disables the ACC4 early stop,
so the larger budget is actually spent.

| system | seed | budget s (base -> ext) | RMSE base | RMSE ext | R2 base | R2 ext | TED base | TED ext | exact base | exact ext |
|---|---|---|---|---|---|---|---|---|---|---|
| CR | 101 | 300 -> 1800 | 1.497 | 1.445 | 0.864 | 0.8734 | 13 | 14 | 0 | 0 |
| CR | 202 | 300 -> 1800 | 1.498 | 1.48 | 0.7111 | 0.7177 | 16 | 16 | 0 | 0 |
| CR | 303 | 300 -> 1800 | 1.481 | 1.481 | 0.6542 | 0.6542 | 14 | 14 | 0 | 0 |
| HCR | 101 | 300 -> 1800 | 1.518 | 3.349e-08 | 0.7795 | 1 | 13 | 0 | 0 | 1 |
| HCR | 202 | 300 -> 1800 | 1.488 | 0.4875 | 0.7459 | 0.9727 | 18 | 8 | 0 | 0 |
| HCR | 303 | 300 -> 1800 | 1.529 | 0.4901 | 0.7273 | 0.972 | 13 | 8 | 0 | 0 |
| MP | 101 | 300 -> 1800 | 3.562 | 3.416 | 0.5675 | 0.6023 | 17 | 15 | 0 | 0 |
| MP | 202 | 300 -> 1800 | 4.226 | 3.841 | 0.5821 | 0.6548 | 19 | 16 | 0 | 0 |
| MP | 303 | 300 -> 1800 | 6.722 | 5.616 | 0.4847 | 0.6402 | 18 | 15 | 0 | 0 |

## Summary

- paired runs compared: 9
- fit error improved: 8
- TED improved: 6
- newly exact at the larger budget: 1

A system whose fit error was already near zero at the small budget cannot be search-limited: the reward was already maximised, so the failure to recover the true formula is one of identifiability, not compute. Only systems whose fit error was large at the small budget can be tested for search limitation here.


# GPU_RUN5 GRN benchmark report（Result B）

Run: `gpu_run5_20260823_ddd267b0`。

**Go 8 は NO-GO だったため、DREAM4・実データへの追加実験は実施しなかった。** 性能不足をデータ側の難しさと混同しないための事前固定停止であり、Phase 8の一度限りのfinal testは負／混合結果として保持する。

## 事実

- Phase 3 status: complete
- validation cells: 960
- true exponent-aware skeleton in beam率: 0
- P6: **hit**、観測値: `{"ci95_upper": -0.08233482545447174, "mean_clustered_difference": -0.20278317058525763, "n_system_clusters": 80, "student_t_95_ci": [-0.3232315157160435, -0.08233482545447174]}`
- P3: **hit**、P4: **hit**。test未開封なら両者は判定不能のまま残す。

## 代表式（成功と失敗を同時掲載）

| 種別 | cell | 真式 | 予測生式 | failure |
|---|---|---|---|---|
| valid_but_structurally_wrong | R01_validation_d101_000_b0_n0_r0 | `0.1954 + 0.8878 * x_0 * 1/(0.8392 + x_0) + -1 * 0.3968 * x_0` | `0.4372 * sin(14.4200 + 0.6135 * x_0) + -0.0191 * (12.7700 + 2.6640 * x_0)**-1` | — |
| valid_but_structurally_wrong | R01_validation_d101_000_b0_n0_r0p5 | `0.1954 + 0.8878 * x_0 * 1/(0.8392 + x_0) + -1 * 0.3968 * x_0` | `0.5096 + -0.2430 * x_0` | — |
| valid_but_structurally_wrong | R01_validation_d101_000_b0_n0p05_r0 | `0.1954 + 0.8878 * x_0 * 1/(0.8392 + x_0) + -1 * 0.3968 * x_0` | `0.3787 * sin(13.7700 + 0.7903 * x_0) + -0.0629 * x_0` | — |
| valid_but_structurally_wrong | R01_validation_d101_000_b0_n0p05_r0p5 | `0.1954 + 0.8878 * x_0 * 1/(0.8392 + x_0) + -1 * 0.3968 * x_0` | `0.4867 + -0.2233 * x_0` | — |
| valid_but_structurally_wrong | R01_validation_d101_000_b1_n0_r0 | `0.1954 + 0.8878 * x_0 * 1/(0.8392 + x_0) + -1 * 0.3968 * x_0` | `0.4444 * sin(14.1100 + 0.3776 * x_0) + -0.1437 * x_0` | — |
| generation_or_evaluation_failure | odebench_20\|n0.05\|r0.0 | `c_0 - c_1 * x_0 + x_0^2 / (1 + x_0^2)` | `5.4542 * (0.2049 + -1 * x_0)**2 + -0.0373 * sin(0.1544 + 23.2011 * x_0)` | NaN |
| generation_or_evaluation_failure | odebench_21\|n0.0\|r0.0 | `c_0 - c_1 * x_0 - exp(-x_0)` | `0.9000 * x_0 * (1.0180 * (x_0)**-1 + -0.0504 * x_0)` | CandidateIntegrationFailure |
| generation_or_evaluation_failure | odebench_21\|n0.0\|r0.5 | `c_0 - c_1 * x_0 - exp(-x_0)` | `9.3411 * x_0 + -9.7360 * x_0 * (0.1553 * x_0 + 1.1080 * (x_0)**-1)` | CandidateIntegrationFailure |
| generation_or_evaluation_failure | odebench_21\|n0.05\|r0.0 | `c_0 - c_1 * x_0 - exp(-x_0)` | `1.1385 * x_0 + -10.8540 * x_0 * (0.0510 * x_0 + 11.7200 * x_0 * (0.0532 * (-0.1065 + -1.2260 * x_0)**-1 + 0.1013 * (x_0)**-1))` | CandidateIntegrationFailure |
| generation_or_evaluation_failure | odebench_21\|n0.05\|r0.5 | `c_0 - c_1 * x_0 - exp(-x_0)` | `9.2520 * x_0 + -9.4140 * x_0 * (0.1105 * x_0 + 1.2540 * (x_0)**-1)` | CandidateIntegrationFailure |
| generation_or_evaluation_failure | R05_validation_d101_006\|b0\|n0p050000000000000003\|r0 | `0.1351 + 1.351 * x_1 * 1/(0.6132 + x_1) + -1 * 0.6607 * x_0 \| 0.1351 + 1.123 * x_0 * 1/(1.07 + x_0) + -1 * 0.6018 * x_1` | `` | ParseError |
| valid_but_structurally_wrong | R06_validation_d101_000\|b0\|n0p050000000000000003\|r0 | `2.136 * 1/(1.172 + x_2) + -1 * 0.7159 * x_0 \| 1.149 * 1/(1.023 + x_0) + -1 * 0.3261 * x_1 \| 0.9279 * 1/(0.5475 + x_1) + -1 * 0.568 * x_2` | `0.2138 * x_1 + -0.1992 * x_0 \| 0.0328 * (-0.1207 + 0.1818 * x_1)**-1 + -0.1479 * x_0 \| -0.0715 * (x_2)**2` | — |
| generation_or_evaluation_failure | R06_validation_d101_002\|b1\|n0p050000000000000003\|r0p5 | `0.291 * 1/(0.1441 + ((x_2)**2)**2) + -1 * 0.4896 * x_0 \| 0.2048 * 1/(0.09381 + ((x_0)**2)**2) + -1 * 0.4279 * x_1 \| 0.8879 * 1/(0.3602 + ((x_1)**2)**2) + -1 * 0.4016 * x_2` | `` | ParseError |
| valid_but_structurally_wrong | R06_validation_d101_000\|b0\|n0p050000000000000003\|r0 | `2.136 * 1/(1.172 + x_2) + -1 * 0.7159 * x_0 \| 1.149 * 1/(1.023 + x_0) + -1 * 0.3261 * x_1 \| 0.9279 * 1/(0.5475 + x_1) + -1 * 0.568 * x_2` | `0.2138 * x_1 + -0.1992 * x_0 \| 0.0328 * (-0.1207 + 0.1818 * x_1)**-1 + -0.1479 * x_0 \| -0.0715 * (x_2)**2` | — |
| final_test_generation_or_evaluation_failure | R02_test_d101_002\|b2\|n0\|r0 | `0.3338 * 1/(0.2837 + ((x_0)**2)**2) + -1 * 0.6123 * x_0` | `` | ParseError |
| final_test_success | R01_test_d101_000\|b0\|n0\|r0 | `0.1933 + 0.8218 * x_0 * 1/(1.402 + x_0) + -1 * 0.5138 * x_0` | `0.0992 + -0.7579 * x_0 + 1.0998 * x_0 * (1.3800 + 1.0005 * x_0)**-1` | — |
| final_test_valid_but_structurally_wrong | R07_test_d101_000\|b0\|n0p050000000000000003\|r0 | `1.202 + -1 * 0.4753 * x_0 \| 1.782 * x_0 * 1/(0.7376 + x_0) + -1 * 0.7211 * x_1 \| 1.794 * x_0 * 1/(0.7719 + x_0) * 1 * x_1 * 1/(0.7376 + x_1) + -1 * 0.5228 * x_2` | `0.2272 * (-0.1040 + 0.5038 * x_0)**-1 + -0.0674 * x_0 \| 0.2226 * (0.1167 + 0.0694 * x_1)**-1 + -0.4878 * x_1 \| 0.0420 * x_0 + -0.0491 * x_2` | — |
| generation_or_evaluation_failure | R06_validation_d101_001\|b0\|n0p050000000000000003\|r0p5 | `2.337 * 1/(1.768 + (x_2)**2) + -1 * 0.8044 * x_0 \| 0.4139 * 1/(0.2944 + (x_0)**2) + -1 * 0.4683 * x_1 \| 0.8696 * 1/(0.6562 + (x_1)**2) + -1 * 0.5906 * x_2` | `0.9352 * x_1 + -0.6450 * (x_0)**2 \| 0.4328 * x_2 + -0.6649 * x_1` | TEDParseError |
| valid_but_structurally_wrong | R06_validation_d101_000\|b0\|n0p050000000000000003\|r0 | `2.136 * 1/(1.172 + x_2) + -1 * 0.7159 * x_0 \| 1.149 * 1/(1.023 + x_0) + -1 * 0.3261 * x_1 \| 0.9279 * 1/(0.5475 + x_1) + -1 * 0.568 * x_2` | `0.2138 * x_1 + -0.1992 * x_0 \| 0.0328 * (-0.1207 + 0.1818 * x_1)**-1 + -0.1479 * x_0 \| -0.0715 * (x_2)**2` | — |

変数とsynthetic gene名の対応を含む全例は `graphs/gpu_run5_20260823_ddd267b0/tables/phase9_formula_examples.csv` に保存した。

## RQ判定

P6はsystem-cluster単位のpaired Student-t 95%区間で判定する。P3/P4はPhase 8 main testのfrozen条件を一度だけ開いた場合だけ判定する。

## 考察

数値fitと指数込み構造回復は別結果として読む。family-holdout R07/R08はmain testの部分集合であり、独立な第二testではない。

## 限界

failure-aware penaltyを主集計へ含め、valid式だけの条件付き性能と混同しない。

## 未実施提案

追加ICや探索budgetの変更は本test後に選び直さず、次campaignで固定する。

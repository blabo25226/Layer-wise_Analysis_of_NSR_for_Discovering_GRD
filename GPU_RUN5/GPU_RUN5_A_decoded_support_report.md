# GPU_RUN5 decoded support report（Result A）

Run: `gpu_run5_20260823_ddd267b0`。数値はmanifest hashで検証した保存済みrecordだけから生成した。

**Go 8 は NO-GO だったため、DREAM4・実データへの追加実験は実施しなかった。** 性能不足をデータ側の難しさと混同しないための事前固定停止であり、Phase 8の一度限りのfinal testは負／混合結果として保持する。

## 事実

- candidate数: 12600
- variable-denominator candidate率: 0.147619
- rateのcount / denominator / 記述的Wilson 95%区間: `{"all_group_truth_in_beam": {"interval_kind": "descriptive_naive_Bernoulli_interval", "rate": 0.015873015873015872, "successes": 4, "total": 252, "wilson_95_ci": [0.006189571180543699, 0.040094791312062256]}, "candidate_variable_denominator": {"interval_kind": "descriptive_naive_Bernoulli_interval", "rate": 0.14761904761904762, "successes": 1860, "total": 12600, "wilson_95_ci": [0.1415327503932974, 0.15392014553428465]}, "variable_group_truth_in_beam": {"interval_kind": "descriptive_naive_Bernoulli_interval", "rate": 0.0, "successes": 0, "total": 56, "wilson_95_ci": [6.938893903907228e-18, 0.06419393671876342]}, "variable_selected_exponent_exact": {"interval_kind": "descriptive_naive_Bernoulli_interval", "rate": 0.0, "successes": 0, "total": 56, "wilson_95_ci": [6.938893903907228e-18, 0.06419393671876342]}}`
- 変数分母56 cellのselected exponent-aware exact件数: 0
- R1 truth form component counts: `{"algebraically_rational": 94, "hill_form": 8, "modulated_hill_form": 4, "rational_with_variable_denominator": 13, "sigmoid_saturating_form": 5, "variable_denominator_form": 20}`
- R2 support denominators: `{"beam_group_any": {"success": 108, "total": 252}, "candidate_occurrence": {"success": 1860, "total": 12600}, "unique_exponent_skeletons_per_beam_mean": 9.277777777777779, "variable_truth_beam_group_any": {"success": 23, "total": 56}, "variable_truth_selected": {"success": 7, "total": 56}}`
- R3 rational-with-variable-denominator vs other: `{"other": {"evaluation_success_rate": 0.875, "exponent_aware_skeleton_exact_rate": 0.018518518518518517, "failure_counts": {"CandidateIntegrationFailure": 10, "NaN": 17, "none": 189}, "failure_penalized_normalized_ted_mean": 0.4326641242101176, "formula_parse_valid_rate": 1.0, "generalization_r2_finite_count": 191, "generalization_r2_mean": -2.4766570390720957, "generalization_r2_median": 0.6838609865399674, "n": 216, "normalized_ted_finite_count": 216, "normalized_ted_mean": 0.4326641242101176, "normalized_ted_median": 0.4508064516129032, "reconstruction_r2_finite_count": 196, "reconstruction_r2_mean": -7.738323767896129, "reconstruction_r2_median": 0.9769694708414844, "record_valid_rate": 0.9074074074074074, "skeleton_exact_rate": 0.08796296296296297}, "rational_with_variable_denominator": {"evaluation_success_rate": 0.9722222222222222, "exponent_aware_skeleton_exact_rate": 0.0, "failure_counts": {"NaN": 1, "none": 35}, "failure_penalized_normalized_ted_mean": 0.5128509129650977, "formula_parse_valid_rate": 1.0, "generalization_r2_finite_count": 35, "generalization_r2_mean": -9.614052596265372, "generalization_r2_median": 0.7101415125215047, "n": 36, "normalized_ted_finite_count": 36, "normalized_ted_mean": 0.5128509129650977, "normalized_ted_median": 0.5185185185185185, "reconstruction_r2_finite_count": 36, "reconstruction_r2_mean": 0.7269997611741378, "reconstruction_r2_median": 0.993194543774478, "record_valid_rate": 1.0, "skeleton_exact_rate": 0.0}}`
- R4: **hit**、R5: **hit**。

## RQ判定

Result Aは、モデルが変数分母候補を出せるかと、その候補から正しい指数込み構造を選べるかを分ける。R4/R5の機械判定は `phase9/preregistration_outcome.json` を正とする。

## 考察

候補内supportは事前学習分布そのものの証明ではなく、固定beam・固定corruption下のdecoded supportである。

## 限界

GPU_RUN4の保存済み252 cell再解析であり、新規推論ではない。selected成功例だけでなく全failureを集計へ残した。

## 未実施提案

beam budgetを変える追試は次runとして事前固定し、本runへ事後追加しない。

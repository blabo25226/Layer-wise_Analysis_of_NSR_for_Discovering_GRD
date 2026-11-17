# GPU_RUN5 GRN adaptation report（Result C）

Run: `gpu_run5_20260823_ddd267b0`。

**Go 8 は NO-GO だったため、DREAM4・実データへの追加実験は実施しなかった。** 性能不足をデータ側の難しさと混同しないための事前固定停止であり、Phase 8の一度限りのfinal testは負／混合結果として保持する。

## 事実

- Phase 6: complete
- Phase 7: complete
- Phase 8 validation: complete
- Go 6: `{"beats_frozen": true, "frozen_score": [0.035590277778, -0.479589420733, 1.0, -6.996191690365], "grn_top3_score": [0.118229166667, -0.467220691306, 0.99375, -1.526271544149], "n_random_sets_beaten": 3, "pass": true, "quantization_digits": 12, "random_scores": {"grn_random3_0": [0.122048611111, -0.448018279089, 1.0, -1.400738760084], "grn_random3_1": [0.050173611111, -0.468276534259, 1.0, -2.434199471523], "grn_random3_2": [0.125173611111, -0.47490654528, 1.0, -1.955149622137], "grn_random3_3": [0.1140625, -0.453118855496, 0.996875, -1.399557982882], "grn_random3_4": [0.109548611111, -0.469205057402, 0.975, -1.361918801814]}, "random_sets_beaten": ["grn_random3_1", "grn_random3_3", "grn_random3_4"], "required_random_sets_beaten": 3, "rule": "grn_top3_strictly_beats_frozen_and_at_least_3_of_5_random3_on_main_validation_formula_score", "test_accessed": false}`
- Go 7: `{"checks": {"all_upstream_phases_prove_test_unopened": true, "both_views_frozen_separately": true, "candidate_budget_beam50": true, "exact_preregistered_final_conditions": true, "freeze_hash_matches_disk": true, "freeze_itself_proves_test_unopened": true, "generalization_not_used_for_selection": true, "go6_passed": true, "three_bundles_frozen": true}, "pass": true, "test_accessed": false}`
- Go 8: `{"checks": {"P6_supported": true, "family_holdout_top3_improves_exact_or_ted": false, "main_generalization_nrmse_ratio_within_limit": false, "main_valid_rate_drop_within_limit": true, "main_validation_top3_beats_frozen_and_3_of_5_random": true, "nontrivial_R03_R08_exact_recovered": false}, "family_holdout_is_subset_not_independent_evidence": true, "family_holdout_label": "system-structure-OOD_partial-component-overlap", "generalization_nrmse_ratio_top3_over_frozen": 1.6275245387571657, "pass": false, "valid_rate_drop_frozen_minus_top3": 0.007291666666666696}`
- Phase 8 final: complete
- sealed test remained unopened: False
- P7: **miss**、観測値: `{"formula_vectors": {"grn_full": [0.1597222222222222, -0.3797548470189649, 0.9642361111111111], "grn_top3": [0.109375, -0.47037921133265165, 0.9927083333333333]}, "grn_top3_forgetting_less_than_grn_full": true, "grn_top3_formula_better_than_grn_full": false, "odebench_forgetting": {"frozen_exact_rate": 0.08465608465608465, "grn_full_drop": 0.07671957671957672, "grn_full_exact_rate": 0.007936507936507936, "grn_top3_drop": 0.023809523809523808, "grn_top3_exact_rate": 0.06084656084656084, "paired_cell_identity_and_audit_valid": true}}`

| stage | view | condition | exact macro | failure-aware TED | valid rate | exact descriptive Wilson | valid descriptive Wilson | exact seed-macro t 95% CI | TED seed-macro t 95% CI | generalization NRMSE seed-macro t 95% CI |
|---|---|---|---:|---:|---:|---|---|---|---|---|
| final_test | main | frozen | 0.0239583 | 0.479168 | 1 | [0.023349009548887464, 0.03822203759745296] | [0.9981204712312125, 1.0] | [0.019293392763063223, 0.02862327390360344] | [0.46817112505845837, 0.4850625049233116] | [1.3218199937142712, 1.4934625684368636] |
| final_test | main | official_continued_full | 0.0597222 | 0.46147 | 1 | [0.06253256655669362, 0.08515083497037887] | [0.9981204712312125, 1.0] | [0.04715593362184074, 0.07228851082260368] | [0.44020834983068635, 0.4780314071983195] | [1.3279676045845348, 1.5568266872747218] |
| final_test | main | grn_full | 0.159722 | 0.368652 | 0.971569 | [0.18463358602641702, 0.21942977967965324] | [0.9634225586413273, 0.97794204265713] | [0.11791088964232378, 0.20153355480212065] | [0.19100014597779846, 0.5685095480601313] | [1.9953409404224485, 2.401093228516871] |
| final_test | main | grn_top3 | 0.109375 | 0.461113 | 0.991176 | [0.12113522584895062, 0.15082395984122385] | [0.9860951646029211, 0.9944114159595053] | [0.011274641715015701, 0.2074753582849843] | [0.449462521815776, 0.4912959008495273] | [-1.0336454999637827, 5.6155869533999] |
| final_test | main | grn_random3_0 | 0.107639 | 0.442226 | 1 | [0.12020199320586956, 0.14980009352110646] | [0.9981204712312125, 1.0] | [0.035169471294324586, 0.18010830648345316] | [0.43397061545125487, 0.4635112060385325] | [0.8967742630393125, 1.6403966281795108] |
| final_test | family_holdout | frozen | 0.0625 | 0.488173 | 1 | [0.04703558611408132, 0.08260807780865623] | [0.9946929555168715, 1.0] | [0.05214942620116855, 0.07285057379883145] | [0.4790760573975027, 0.4972695854629495] | [0.785821578169865, 1.0767963634603661] |
| final_test | family_holdout | official_continued_full | 0.143056 | 0.470442 | 1 | [0.11937288294533838, 0.17052686825511737] | [0.9946929555168715, 1.0] | [0.11317602271044344, 0.17293508840066765] | [0.45041230470090876, 0.49047151222431684] | [0.5924339595431567, 0.7698843879856225] |
| final_test | family_holdout | grn_full | 0.1875 | 0.456722 | 1 | [0.1606760793258498, 0.21764082347610567] | [0.9946929555168715, 1.0] | [0.14238289480323385, 0.23261710519676615] | [0.4509126143457707, 0.46253115397163225] | [0.4835822862624544, 0.503018806940807] |
| final_test | family_holdout | grn_top3 | 0.0527778 | 0.491448 | 1 | [0.03869081608585858, 0.07161159592405089] | [0.9946929555168715, 1.0] | [-0.061235253026132745, 0.1667908085816883] | [0.4412376807358332, 0.5416577827292134] | [0.44097287497240195, 0.6339638733049316] |
| final_test | family_holdout | grn_random3_0 | 0.0347222 | 0.501955 | 1 | [0.023627872772985645, 0.05075507139881459] | [0.9946929555168715, 1.0] | [0.022770409084177375, 0.046674035360267055] | [0.4954835351074482, 0.5084265585268446] | [0.7818134406233987, 1.0084487404360505] |

Wilson区間は反復corruptionを含むcomponentをBernoulli試行として数えた**記述的なnaive区間**であり、独立systemに対する推測区間ではない。seed-macro区間はsystem内を先に平均した3 seedsのStudent-t区間であり、少数seedのため非常に広くなり得る。同じsystem corpusを3 seedsで共有するためsystem sampling uncertaintyは含まない。

## RQ判定

P7はmain testで `grn_top3` と `grn_full` のformula scoreを事前順序でlexicographic比較し、同時にODEBench exponent-aware exactのfrozenからの低下を比較する。片方でも欠ければ判定不能である。

## 考察

official-continuedは追加学習一般、GRN fullはdomain adaptation、selectiveは適応先の効果を分ける対照である。

## 限界

ODEBench forgettingはsecondary outcomeで選択に使っていない。異なるモデル・世代の絶対scoreは比較しない。

## 未実施提案

Go 6不成立でtestを開かなかった場合、P3/P4/P7を埋めるためだけの事後条件追加は行わない。

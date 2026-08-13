"""Layer interpretability helpers for GPU_RUN2 (probe, CKA, DecoderLens, interventions)."""

from .cka import linear_cka
from .decoder_lens import (
    DecoderLensStep,
    apply_final_encoder_pool,
    encoder_memory_at_layer,
    prefix_tokens_to_equation,
    run_decoder_lens,
    summarize_decoder_lens_steps,
    write_decoder_lens_rank_heatmap,
)
from .interventions import (
    ablation_zero_output,
    interpolate_activations,
    register_replace_output_hook,
    register_zero_output_hook,
    replace_output_context,
    zero_output_context,
)
from .probes import (
    expression_structure_attributes,
    fit_linear_classifier_probe,
    fit_linear_probe,
    gradient_norms,
    mean_rank_layer_scores,
    parameter_update_sensitivity,
    ranking_from_mean_rank,
)

__all__ = [
    "DecoderLensStep",
    "ablation_zero_output",
    "apply_final_encoder_pool",
    "encoder_memory_at_layer",
    "expression_structure_attributes",
    "fit_linear_classifier_probe",
    "fit_linear_probe",
    "gradient_norms",
    "mean_rank_layer_scores",
    "ranking_from_mean_rank",
    "interpolate_activations",
    "linear_cka",
    "parameter_update_sensitivity",
    "prefix_tokens_to_equation",
    "register_replace_output_hook",
    "register_zero_output_hook",
    "replace_output_context",
    "run_decoder_lens",
    "summarize_decoder_lens_steps",
    "write_decoder_lens_rank_heatmap",
    "zero_output_context",
]

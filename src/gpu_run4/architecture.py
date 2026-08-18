"""ODEFormer architecture inventory and paper / parser / checkpoint audit."""

from __future__ import annotations

from typing import Any, Mapping

PAPER_ARCHITECTURE = {
    "n_encoder_layers": 4,
    "n_decoder_layers": 16,
    "embedding_dim": 512,
    "n_attention_heads": 16,
    "approx_total_parameters": 86_000_000,
    "encoder_positional_embeddings": None,
}

# Source: third_party/odeformer/parsers.py argument defaults.
# These are NOT the architecture of the released checkpoint.
PARSER_DEFAULTS = {
    "n_enc_layers": 4,
    "n_dec_layers": 12,
    "enc_emb_dim": 256,
    "dec_emb_dim": 256,
    "n_enc_heads": 16,
    "n_dec_heads": 16,
    "beam_size": 1,
    "beam_type": "sampling",
    "beam_temperature": 0.1,
    "enc_positional_embeddings": None,
    "share_inout_emb": True,
}

# Source: third_party/odeformer/odeformer/model/model_wrapper.py __init__ defaults.
MODEL_WRAPPER_INIT_DEFAULTS = {
    "beam_type": "search",
    "beam_size": 1,
    "beam_temperature": 1.0,
}

CONTROL_MODULE_PREFIXES = (
    "embedder",
    "encoder.embeddings",
    "encoder.position_embeddings",
    "encoder.layer_norm_emb",
    "decoder.embeddings",
    "decoder.position_embeddings",
    "decoder.layer_norm_emb",
    "decoder.proj",
)


def unwrap_model(model: Any) -> Any:
    """Return the ModelWrapper-like object that owns encoder / decoder."""
    if hasattr(model, "encoder") and hasattr(model, "decoder"):
        return model
    inner = getattr(model, "model", None)
    if inner is not None and hasattr(inner, "encoder") and hasattr(inner, "decoder"):
        return inner
    raise RuntimeError("ArchitectureMismatch: object has no encoder/decoder")


def _module_role(name: str) -> str:
    if name.startswith("embedder"):
        return "embedder"
    if name.startswith("encoder"):
        if any(token in name for token in ("embeddings", "position_embeddings", "layer_norm_emb")):
            return "embedding"
        return "encoder"
    if name.startswith("decoder"):
        if name.startswith("decoder.proj") or name.endswith(".proj"):
            return "head"
        if any(token in name for token in ("embeddings", "position_embeddings", "layer_norm_emb")):
            return "embedding"
        return "decoder"
    return "other"


def _layer_index_from_name(name: str) -> int | None:
    parts = name.split(".")
    for part in reversed(parts):
        if part.isdigit():
            return int(part)
    return None


def _is_control_module(name: str) -> bool:
    return any(name == prefix or name.startswith(prefix + ".") for prefix in CONTROL_MODULE_PREFIXES)


def ranking_layer_names(n_encoder: int, n_decoder: int) -> list[str]:
    return [f"encoder_{i}" for i in range(n_encoder)] + [f"decoder_{i}" for i in range(n_decoder)]


def _block_parameter_count(named_parameters: Mapping[str, Any], prefixes: tuple[str, ...]) -> int:
    total = 0
    for name, parameter in named_parameters.items():
        if any(name.startswith(prefix) for prefix in prefixes):
            total += int(parameter.numel())
    return total


def _encoder_block_prefixes(index: int) -> tuple[str, ...]:
    return (
        f"encoder.attentions.{index}.",
        f"encoder.layer_norm1.{index}.",
        f"encoder.ffns.{index}.",
        f"encoder.layer_norm2.{index}.",
    )


def _decoder_block_prefixes(index: int) -> tuple[str, ...]:
    return (
        f"decoder.attentions.{index}.",
        f"decoder.layer_norm1.{index}.",
        f"decoder.layer_norm15.{index}.",
        f"decoder.encoder_attn.{index}.",
        f"decoder.ffns.{index}.",
        f"decoder.layer_norm2.{index}.",
    )


def inventory_odeformer(model: Any) -> dict[str, Any]:
    """Walk the released ODEFormer and classify Transformer blocks vs control modules."""
    import torch

    wrapped = unwrap_model(model)
    encoder = wrapped.encoder
    decoder = wrapped.decoder
    n_encoder = int(encoder.n_layers)
    n_decoder = int(decoder.n_layers)
    encoder_dim = int(encoder.dim)
    decoder_dim = int(decoder.dim)
    encoder_heads = int(encoder.n_heads)
    decoder_heads = int(decoder.n_heads)

    named_parameters = dict(wrapped.named_parameters())
    rows: list[dict[str, Any]] = []
    control_layers: list[str] = []
    for name, module in wrapped.named_modules():
        if name == "":
            continue
        n_params = sum(p.numel() for p in module.parameters(recurse=False))
        trainable = any(p.requires_grad for p in module.parameters(recurse=False))
        row = {
            "module_name": name,
            "module_type": type(module).__name__,
            "role": _module_role(name),
            "layer_index": _layer_index_from_name(name),
            "parameter_count": int(n_params),
            "trainable": bool(trainable),
            "has_children": any(True for _ in module.children()),
            "self_attention": name.startswith(("encoder.attentions.", "decoder.attentions.")),
            "cross_attention": name.startswith("decoder.encoder_attn."),
            "ffn": name.startswith(("encoder.ffns.", "decoder.ffns.")),
            "normalization": "layer_norm" in name,
        }
        rows.append(row)
        if _is_control_module(name) and n_params > 0 and not row["has_children"]:
            control_layers.append(name)

    encoder_blocks = []
    decoder_blocks = []
    for index in range(n_encoder):
        encoder_blocks.append(
            {
                "ranking_name": f"encoder_{index}",
                "layer_index": index,
                "module_group": "encoder",
                "parameter_count": _block_parameter_count(named_parameters, _encoder_block_prefixes(index)),
                "hidden_dim": encoder_dim,
                "n_heads": encoder_heads,
                "self_attention": True,
                "cross_attention": False,
                "modules": [
                    f"encoder.attentions.{index}",
                    f"encoder.layer_norm1.{index}",
                    f"encoder.ffns.{index}",
                    f"encoder.layer_norm2.{index}",
                ],
            }
        )
    for index in range(n_decoder):
        decoder_blocks.append(
            {
                "ranking_name": f"decoder_{index}",
                "layer_index": index,
                "module_group": "decoder",
                "parameter_count": _block_parameter_count(named_parameters, _decoder_block_prefixes(index)),
                "hidden_dim": decoder_dim,
                "n_heads": decoder_heads,
                "self_attention": True,
                "cross_attention": True,
                "modules": [
                    f"decoder.attentions.{index}",
                    f"decoder.layer_norm1.{index}",
                    f"decoder.layer_norm15.{index}",
                    f"decoder.encoder_attn.{index}",
                    f"decoder.ffns.{index}",
                    f"decoder.layer_norm2.{index}",
                ],
            }
        )

    proj = getattr(decoder, "proj", None)
    embeddings = getattr(decoder, "embeddings", None)
    tied_embedding = False
    if proj is not None and embeddings is not None and hasattr(proj, "weight") and hasattr(embeddings, "weight"):
        tied_embedding = proj.weight.data_ptr() == embeddings.weight.data_ptr()

    encoder_pos = getattr(encoder, "position_embeddings", None)
    total_parameters = int(sum(p.numel() for p in wrapped.parameters()))
    return {
        "n_encoder_transformer_layers": n_encoder,
        "n_decoder_transformer_layers": n_decoder,
        "encoder_embedding_dim": encoder_dim,
        "decoder_embedding_dim": decoder_dim,
        "encoder_n_heads": encoder_heads,
        "decoder_n_heads": decoder_heads,
        "encoder_positional_embeddings": encoder_pos is not None,
        "decoder_n_words": int(getattr(decoder, "n_words", 0) or 0),
        "tied_output_embedding": bool(tied_embedding),
        "beam_size": getattr(wrapped, "beam_size", None),
        "beam_temperature": getattr(wrapped, "beam_temperature", None),
        "beam_type": getattr(wrapped, "beam_type", None),
        "ranking_layers": ranking_layer_names(n_encoder, n_decoder),
        "encoder_blocks": encoder_blocks,
        "decoder_blocks": decoder_blocks,
        "control_layers": sorted(set(control_layers)),
        "modules": rows,
        "device": str(next(wrapped.parameters()).device),
        "dtype": str(next(wrapped.parameters()).dtype),
        "total_parameters": total_parameters,
        "embedder_type": type(getattr(wrapped, "embedder", None)).__name__,
        "torch": torch.__version__,
        "n_ranking_layers": n_encoder + n_decoder,
    }


def architecture_audit(inventory: Mapping[str, Any], *, paper: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Compare checkpoint inventory to the paper table. Parser defaults are recorded separately."""
    expected = dict(paper or PAPER_ARCHITECTURE)
    mismatches: list[dict[str, Any]] = []

    def _check(field: str, observed: Any, target: Any) -> None:
        if observed != target:
            mismatches.append({"field": field, "observed": observed, "paper": target})

    _check("n_encoder_layers", inventory.get("n_encoder_transformer_layers"), expected["n_encoder_layers"])
    _check("n_decoder_layers", inventory.get("n_decoder_transformer_layers"), expected["n_decoder_layers"])
    _check("embedding_dim", inventory.get("encoder_embedding_dim"), expected["embedding_dim"])
    _check("decoder_embedding_dim", inventory.get("decoder_embedding_dim"), expected["embedding_dim"])
    _check("n_attention_heads", inventory.get("encoder_n_heads"), expected["n_attention_heads"])
    _check("decoder_n_heads", inventory.get("decoder_n_heads"), expected["n_attention_heads"])
    if bool(inventory.get("encoder_positional_embeddings")) != bool(expected["encoder_positional_embeddings"]):
        mismatches.append(
            {
                "field": "encoder_positional_embeddings",
                "observed": inventory.get("encoder_positional_embeddings"),
                "paper": expected["encoder_positional_embeddings"],
            }
        )

    total = inventory.get("total_parameters")
    approx = int(expected["approx_total_parameters"])
    parameter_band_ok = total is not None and abs(int(total) - approx) <= int(0.20 * approx)
    if not parameter_band_ok:
        mismatches.append(
            {
                "field": "approx_total_parameters",
                "observed": total,
                "paper": approx,
                "note": "paper reports ~86M; fail if outside ±20%",
            }
        )

    parser_diffs = {
        "n_dec_layers": {
            "parser": PARSER_DEFAULTS["n_dec_layers"],
            "paper": expected["n_decoder_layers"],
            "checkpoint": inventory.get("n_decoder_transformer_layers"),
        },
        "enc_emb_dim": {
            "parser": PARSER_DEFAULTS["enc_emb_dim"],
            "paper": expected["embedding_dim"],
            "checkpoint": inventory.get("encoder_embedding_dim"),
        },
        "dec_emb_dim": {
            "parser": PARSER_DEFAULTS["dec_emb_dim"],
            "paper": expected["embedding_dim"],
            "checkpoint": inventory.get("decoder_embedding_dim"),
        },
        "beam_size": {
            "parser": PARSER_DEFAULTS["beam_size"],
            "paper": 50,
            "checkpoint": inventory.get("beam_size"),
            "model_wrapper_init": MODEL_WRAPPER_INIT_DEFAULTS["beam_size"],
        },
        "beam_type": {
            "parser": PARSER_DEFAULTS["beam_type"],
            "paper": "sampling",
            "checkpoint": inventory.get("beam_type"),
            "model_wrapper_init": MODEL_WRAPPER_INIT_DEFAULTS["beam_type"],
        },
        "beam_temperature": {
            "parser": PARSER_DEFAULTS["beam_temperature"],
            "paper": 0.1,
            "checkpoint": inventory.get("beam_temperature"),
            "model_wrapper_init": MODEL_WRAPPER_INIT_DEFAULTS["beam_temperature"],
        },
    }
    return {
        "matches_paper": not mismatches,
        "mismatches": mismatches,
        "parser_vs_paper_vs_checkpoint": parser_diffs,
        "parser_defaults": PARSER_DEFAULTS,
        "paper_architecture": expected,
        "model_wrapper_init_defaults": MODEL_WRAPPER_INIT_DEFAULTS,
    }


def parser_defaults_from_source(parsers_text: str) -> dict[str, Any]:
    """Extract the audited parser defaults from vendored parsers.py text."""
    extracted: dict[str, Any] = {}
    keys = {
        "n_enc_layers": int,
        "n_dec_layers": int,
        "enc_emb_dim": int,
        "dec_emb_dim": int,
        "n_enc_heads": int,
        "n_dec_heads": int,
        "beam_size": int,
        "beam_type": str,
        "beam_temperature": float,
    }
    for key, caster in keys.items():
        marker = f'"{key}"' if f'"{key}"' in parsers_text else f"--{key}"
        idx = parsers_text.find(marker)
        if idx < 0:
            continue
        window = parsers_text[idx : idx + 400]
        default_idx = window.find("default=")
        if default_idx < 0:
            continue
        raw = window[default_idx + len("default=") :].split(",")[0].split(")")[0].strip()
        if raw.startswith(("'", '"')):
            extracted[key] = raw.strip("'\"")
        elif raw in {"None", "True", "False"}:
            extracted[key] = {"None": None, "True": True, "False": False}[raw]
        else:
            extracted[key] = caster(raw)
    return extracted

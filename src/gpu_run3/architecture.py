"""NDformer architecture inventory and trainable-layer taxonomy."""

from __future__ import annotations

from typing import Any

RANKING_PREFIXES = ("encoder.Transformer.layers.", "decoder.decoder.layers.")
CONTROL_PREFIXES = (
    "encoder.GNN.",
    "decoder.token_embedding",
    "decoder.index_embedding",
    "decoder.pe",
    "decoder.value_head",
)


def _module_role(name: str, module: Any) -> str:
    type_name = type(module).__name__
    if name.startswith("encoder.GNN"):
        return "gnn"
    if name.startswith("encoder.Transformer"):
        return "encoder"
    if name.startswith("decoder.decoder"):
        return "decoder"
    if "embedding" in name or name.endswith(".pe"):
        return "embedding"
    if "value_head" in name or type_name == "Linear":
        return "head"
    if name.startswith("encoder"):
        return "encoder"
    if name.startswith("decoder"):
        return "decoder"
    return "other"


def _layer_index(name: str) -> int | None:
    parts = name.split(".")
    for part in reversed(parts):
        if part.isdigit():
            return int(part)
    return None


def inventory_ndformer(model: Any) -> dict[str, Any]:
    """Walk NDformer and classify Transformer blocks vs control modules."""
    import torch
    from torch import nn

    rows: list[dict[str, Any]] = []
    ranking_layers: list[str] = []
    control_layers: list[str] = []
    for name, module in model.named_modules():
        if name == "":
            continue
        n_params = sum(p.numel() for p in module.parameters(recurse=False))
        trainable = any(p.requires_grad for p in module.parameters(recurse=False))
        row = {
            "module_name": name,
            "module_type": type(module).__name__,
            "role": _module_role(name, module),
            "layer_index": _layer_index(name),
            "parameter_count": int(n_params),
            "trainable": bool(trainable),
            "has_children": any(True for _ in module.children()),
        }
        if isinstance(module, nn.TransformerEncoderLayer):
            row["self_attention"] = True
            row["cross_attention"] = False
            row["norm_first"] = bool(getattr(module, "norm_first", False))
            row["residual"] = True
            ranking_layers.append(name)
        elif isinstance(module, nn.TransformerDecoderLayer):
            row["self_attention"] = True
            row["cross_attention"] = True
            row["norm_first"] = bool(getattr(module, "norm_first", False))
            row["residual"] = True
            ranking_layers.append(name)
        rows.append(row)
        if name.startswith(CONTROL_PREFIXES) and n_params > 0 and not row["has_children"]:
            control_layers.append(name)

    encoder_blocks = [name for name, module in model.named_modules() if isinstance(module, nn.TransformerEncoderLayer)]
    decoder_blocks = [name for name, module in model.named_modules() if isinstance(module, nn.TransformerDecoderLayer)]
    return {
        "n_encoder_transformer_layers": len(encoder_blocks),
        "n_decoder_transformer_layers": len(decoder_blocks),
        "n_gnn_layers": len(list(model.encoder.GNN.GNN_layers)),
        "d_emb": int(model.encoder.d_emb),
        "n_words": int(model.decoder.n_words),
        "max_seq_len": int(model.decoder.max_seq_len),
        "ranking_layers": encoder_blocks + decoder_blocks,
        "encoder_blocks": encoder_blocks,
        "decoder_blocks": decoder_blocks,
        "control_layers": sorted(set(control_layers)),
        "modules": rows,
        "device": str(getattr(model, "device", next(model.parameters()).device)),
        "dtype": str(next(model.parameters()).dtype),
        "total_parameters": int(sum(p.numel() for p in model.parameters())),
        "torch": torch.__version__,
    }


def resolve_layer_module(model: Any, layer_name: str) -> Any:
    module = model
    for part in layer_name.split("."):
        if part.isdigit():
            module = module[int(part)]
        else:
            module = getattr(module, part)
    return module


def set_trainable_layers(model: Any, layer_names: list[str] | None, *, train_all: bool = False) -> dict[str, int]:
    """Freeze everything, then enable the selected Transformer blocks (or all parameters)."""
    for parameter in model.parameters():
        parameter.requires_grad = bool(train_all)
    enabled = 0
    if not train_all and layer_names:
        for name in layer_names:
            module = resolve_layer_module(model, name)
            for parameter in module.parameters():
                parameter.requires_grad = True
                enabled += parameter.numel()
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    total = sum(p.numel() for p in model.parameters())
    return {
        "trainable_parameters": int(trainable),
        "total_parameters": int(total),
        "trainable_ratio": float(trainable / total) if total else 0.0,
        "enabled_layer_parameters": int(enabled),
    }

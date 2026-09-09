"""Tests for gpu_runclaude1.partc_reencoding's control flow, using a fake
``env`` stand-in for the odeformer environment object -- no torch, no real
model, no GPU. The fake exercises exactly the three calls the module makes
(``env.simplifier.sympy_expr_to_tree``, ``env.equation_encoder.encode``,
``env.equation_encoder.decode``) and nothing else, so these tests pin the
module's own control flow (parse -> encode -> decode -> canonicalize, and
every named failure path) without needing the vendored ODEFormer package or
a loaded checkpoint.
"""

from __future__ import annotations

from gpu_run4.formulas import join_canonical_system, parse_prefix_component
from gpu_runclaude1.partc_reencoding import infix_to_model_tokens, reencode_infix_via_model


class _FakeNode:
    def __init__(self, prefix_str: str):
        self._prefix_str = prefix_str

    def prefix(self) -> str:
        return self._prefix_str


class _FakeSimplifier:
    """Stands in for env.simplifier: any sympy expr becomes a fake Node
    tagged with the expr's own string form, so the fake encoder/decoder pair
    below can round-trip it deterministically.
    """

    def sympy_expr_to_tree(self, expr):
        return _FakeNode(str(expr))


class _RoundtripEncoder:
    """A "perfect" encoder: encode/decode is a no-op round trip, so the
    reencoded canonical form should exactly match what this repository's own
    canonicalizer produces from the same expression.
    """

    def encode(self, tree):
        return [tree.prefix()]

    def decode(self, tokens):
        return _FakeNode(tokens[0])


class _LossyEncoder:
    """Simulates real precision loss: decode always returns a fixed,
    different tree than whatever was encoded.
    """

    def encode(self, tree):
        return ["TOKEN"]

    def decode(self, tokens):
        return _FakeNode("mul,x_0,x_1")  # deliberately wrong


class _RaisingEncoder:
    def encode(self, tree):
        raise RuntimeError("boom")

    def decode(self, tokens):
        raise AssertionError("should not be reached")


class _NoneDecodeEncoder:
    def encode(self, tree):
        return ["TOKEN"]

    def decode(self, tokens):
        return None


def _fake_env(encoder_cls):
    class _Env:
        simplifier = _FakeSimplifier()
        equation_encoder = encoder_cls()

    return _Env()


def test_reencode_roundtrip_success_matches_repo_canonicalization():
    env = _fake_env(_RoundtripEncoder)
    result = reencode_infix_via_model(env, "x_0 + x_1")
    assert result.failure_reason is None
    assert result.canonical is not None
    # Cross-check against the same repo canonicalization pipeline the module
    # itself calls: since the fake encoder is a no-op round trip, the sympy
    # string form of "x_0 + x_1" run through parse_prefix_component should
    # match what the module produced by going through the fake Node.
    from sympy import sympify

    from gpu_run4.formulas import _sympy_local_dict

    expr_str = str(sympify("x_0 + x_1", locals=_sympy_local_dict()))
    expected_tree = parse_prefix_component(expr_str)
    expected = join_canonical_system([expected_tree])
    assert result.canonical == expected


def test_reencode_parse_failure_on_unparseable_raw():
    env = _fake_env(_RoundtripEncoder)
    result = reencode_infix_via_model(env, "((( not an equation")
    assert result.canonical is None
    assert result.failure_reason == "SkeletonParseFailure"


def test_reencode_encoder_exception_is_skeleton_evaluation_failure():
    env = _fake_env(_RaisingEncoder)
    result = reencode_infix_via_model(env, "x_0 + x_1")
    assert result.canonical is None
    assert result.failure_reason == "SkeletonEvaluationFailure"


def test_reencode_none_decode_is_skeleton_evaluation_failure():
    env = _fake_env(_NoneDecodeEncoder)
    result = reencode_infix_via_model(env, "x_0 + x_1")
    assert result.canonical is None
    assert result.failure_reason == "SkeletonEvaluationFailure"


def test_reencode_lossy_roundtrip_still_produces_a_canonical_string():
    """A "successful" (non-crashing) but lossy round trip is not itself a
    failure at this layer -- the module's job is to produce the reencoded
    canonical form; whether it *matches* the stored one is
    audit_reencoding_roundtrip's job, called separately by the phase script.
    """
    env = _fake_env(_LossyEncoder)
    result = reencode_infix_via_model(env, "x_0 + x_1")
    assert result.failure_reason is None
    assert result.canonical is not None


def test_reencode_multi_component_system_splits_on_separator():
    env = _fake_env(_RoundtripEncoder)
    result = reencode_infix_via_model(env, "x_0 | x_1 + 1")
    assert result.failure_reason is None
    assert ",|," in result.canonical


def test_infix_to_model_tokens_single_component():
    env = _fake_env(_RoundtripEncoder)
    tokens, failure = infix_to_model_tokens(env, "x_0 + x_1")
    assert failure is None
    assert tokens is not None
    assert "|" not in tokens


def test_infix_to_model_tokens_multi_component_joins_with_pipe_token():
    env = _fake_env(_RoundtripEncoder)
    tokens, failure = infix_to_model_tokens(env, "x_0 | x_1")
    assert failure is None
    assert tokens.count("|") == 1


def test_infix_to_model_tokens_parse_failure():
    env = _fake_env(_RoundtripEncoder)
    tokens, failure = infix_to_model_tokens(env, "((( not an equation")
    assert tokens is None
    assert failure == "SkeletonParseFailure"


def test_infix_to_model_tokens_encoder_exception():
    env = _fake_env(_RaisingEncoder)
    tokens, failure = infix_to_model_tokens(env, "x_0 + x_1")
    assert tokens is None
    assert failure == "SkeletonEvaluationFailure"

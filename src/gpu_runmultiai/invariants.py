"""Explicit invariant exceptions that may abort the audit."""

from __future__ import annotations


class AuditInvariantError(RuntimeError):
    """Resume identity, duplicate key, ceiling, or serialization invariant violation."""


class ResumeCacheMissError(AuditInvariantError):
    """Counted call exists in call_log but stage cache payload is missing."""


class StageCacheSerializationError(AuditInvariantError):
    """Stage cache payload cannot be JSON-serialized."""


class ResourceCeilingError(AuditInvariantError):
    """Frozen CPU wall-time or disk budget exceeded."""


class FrozenEnvironmentError(AuditInvariantError):
    """Frozen environment variable does not match the required byte-identical value."""


class CorpusGateError(AuditInvariantError):
    """G_corpus precondition failed before primary audit work."""


class ScalerGateError(AuditInvariantError):
    """G0 scaler assertion failed before primary audit work."""

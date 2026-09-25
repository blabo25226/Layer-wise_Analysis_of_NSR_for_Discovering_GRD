"""Focused tests for .ai/workers/claude.sh (no live Claude API call)."""

from __future__ import annotations

import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CLAUDE_SH = REPO_ROOT / ".ai" / "workers" / "claude.sh"


def test_claude_sh_syntax() -> None:
    proc = subprocess.run(["bash", "-n", str(CLAUDE_SH)], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr


def test_claude_sh_default_model_in_script() -> None:
    text = CLAUDE_SH.read_text(encoding="utf-8")
    assert "claude-opus-5-5" in text
    assert "AI_WORKERS_CLAUDE_MODEL" in text

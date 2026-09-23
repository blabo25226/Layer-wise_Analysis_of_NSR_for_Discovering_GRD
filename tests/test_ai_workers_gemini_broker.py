"""Focused tests for .ai/workers/gemini.sh broker acceptance (no live Antigravity call)."""

from __future__ import annotations

import json
import os
import subprocess
import textwrap
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
GEMINI_SH = REPO_ROOT / ".ai" / "workers" / "gemini.sh"


def _run_broker(
    tmp_path: Path,
    fake_agy: Path,
    prompt_body: str,
    acceptance: str = "non-empty",
) -> subprocess.CompletedProcess[str]:
    prompt_file = tmp_path / "packet.md"
    prompt_file.write_text(prompt_body, encoding="utf-8")
    output_file = tmp_path / "out.md"
    env = os.environ.copy()
    env["AI_WORKERS_ANTIGRAVITY_BIN"] = str(fake_agy)
    env["AI_WORKERS_GEMINI_MODEL"] = "gemini-3.8-flash-high"
    return subprocess.run(
        [
            "bash",
            str(GEMINI_SH),
            "--broker",
            "--prompt-file",
            str(prompt_file),
            "--output-file",
            str(output_file),
            "--acceptance",
            acceptance,
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def test_gemini_sh_syntax() -> None:
    proc = subprocess.run(["bash", "-n", str(GEMINI_SH)], capture_output=True, text=True, check=False)
    assert proc.returncode == 0, proc.stderr


def test_broker_rejects_empty_stdout_despite_zero_exit(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_agy.chmod(0o755)
    proc = _run_broker(tmp_path, fake_agy, "hello")
    assert proc.returncode == 70


def test_broker_persists_artifact_and_provenance(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text(
        textwrap.dedent(
            """#!/bin/sh
cat <<'EOF'
## Evidence
line

## Inference
line

## Speculation
line
EOF
"""
        ),
        encoding="utf-8",
    )
    fake_agy.chmod(0o755)
    proc = _run_broker(tmp_path, fake_agy, "compress this", acceptance="headings")
    assert proc.returncode == 0, proc.stderr
    output_file = tmp_path / "out.md"
    provenance_file = tmp_path / "out.md.provenance.json"
    assert output_file.is_file() and output_file.stat().st_size > 0
    assert provenance_file.is_file()
    record = json.loads(provenance_file.read_text(encoding="utf-8"))
    assert record["mode"] == "broker"
    assert record["model"] == "gemini-3.8-flash-high"
    assert record["acceptance"] == "headings"


def test_broker_headings_acceptance_fails(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text("#!/bin/sh\necho 'no headings'\n", encoding="utf-8")
    fake_agy.chmod(0o755)
    proc = _run_broker(tmp_path, fake_agy, "x", acceptance="headings")
    assert proc.returncode == 71

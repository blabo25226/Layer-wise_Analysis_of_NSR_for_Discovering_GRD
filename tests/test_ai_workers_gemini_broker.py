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
    *,
    prompt_name: str = "prompt.txt",
    output_name: str = "out.md",
    extra_args: list[str] | None = None,
) -> subprocess.CompletedProcess[str]:
    prompt_file = tmp_path / prompt_name
    prompt_file.write_text(prompt_body, encoding="utf-8")
    output_file = tmp_path / output_name
    env = os.environ.copy()
    env["AI_WORKERS_ANTIGRAVITY_BIN"] = str(fake_agy)
    env["AI_WORKERS_GEMINI_MODEL"] = "gemini-3.8-flash-high"
    cmd = [
        "bash",
        str(GEMINI_SH),
        "--broker",
        "--prompt-file",
        str(prompt_file),
        "--output-file",
        str(output_file),
        "--acceptance",
        acceptance,
    ]
    if extra_args:
        cmd.extend(extra_args)
    return subprocess.run(
        cmd,
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


def test_broker_json_rejects_scalar(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text('#!/bin/sh\necho \'"ok"\'\n', encoding="utf-8")
    fake_agy.chmod(0o755)
    output_file = tmp_path / "out.md"
    output_file.write_text("stale artifact\n", encoding="utf-8")
    proc = _run_broker(tmp_path, fake_agy, "x", acceptance="json")
    assert proc.returncode == 72
    assert output_file.read_text(encoding="utf-8") == "stale artifact\n"


def test_broker_json_accepts_object(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text('#!/bin/sh\necho \'{"ok":true}\'\n', encoding="utf-8")
    fake_agy.chmod(0o755)
    proc = _run_broker(tmp_path, fake_agy, "x", acceptance="json")
    assert proc.returncode == 0, proc.stderr


def test_broker_json_rejects_invalid_json(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text("#!/bin/sh\necho 'not-json'\n", encoding="utf-8")
    fake_agy.chmod(0o755)
    proc = _run_broker(tmp_path, fake_agy, "x", acceptance="json")
    assert proc.returncode == 72
    assert not (tmp_path / "out.md").exists()


def test_broker_nonzero_cli_exit_skips_artifact(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text("#!/bin/sh\necho ok\nexit 3\n", encoding="utf-8")
    fake_agy.chmod(0o755)
    proc = _run_broker(tmp_path, fake_agy, "x", acceptance="non-empty")
    assert proc.returncode == 3
    assert not (tmp_path / "out.md").exists()


def test_broker_rejects_deny_marker_despite_zero_exit(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text(
        "#!/bin/sh\necho 'jetski: no output produced — auto-denied'\n",
        encoding="utf-8",
    )
    fake_agy.chmod(0o755)
    output_file = tmp_path / "out.md"
    output_file.write_text("stale artifact\n", encoding="utf-8")
    proc = _run_broker(tmp_path, fake_agy, "x", acceptance="non-empty")
    assert proc.returncode == 73
    assert output_file.read_text(encoding="utf-8") == "stale artifact\n"


def test_broker_rejects_write_flag(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    fake_agy.chmod(0o755)
    proc = _run_broker(tmp_path, fake_agy, "x", extra_args=["--write"])
    assert proc.returncode == 64


def test_broker_unknown_acceptance_rejected_before_agy(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text("#!/bin/sh\necho 'AGY_SHOULD_NOT_RUN'\n", encoding="utf-8")
    fake_agy.chmod(0o755)
    proc = _run_broker(tmp_path, fake_agy, "x", acceptance="bogus-mode")
    assert proc.returncode == 64
    assert "unknown acceptance mode bogus-mode" in proc.stderr
    assert "AGY_SHOULD_NOT_RUN" not in proc.stdout


def test_broker_evidence_packet_requires_headings(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text("#!/bin/sh\necho 'plain text'\n", encoding="utf-8")
    fake_agy.chmod(0o755)
    proc = _run_broker(
        tmp_path,
        fake_agy,
        "x",
        acceptance="non-empty",
        prompt_name="review_evidence.md",
        output_name="out.md",
    )
    assert proc.returncode == 74


def test_direct_write_blocked_without_fs_e2e_marker(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text("#!/bin/sh\nexit 0\n", encoding="utf-8")
    fake_agy.chmod(0o755)
    env = os.environ.copy()
    env["AI_WORKERS_ANTIGRAVITY_BIN"] = str(fake_agy)
    env["AI_WORKERS_GEMINI_FS_E2E_PASS_FILE"] = str(tmp_path / "missing.pass")
    proc = subprocess.run(
        ["bash", str(GEMINI_SH), "--write", "probe"],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 78


def test_broker_mkdir_failure_is_fail_closed(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text("#!/bin/sh\necho ok\n", encoding="utf-8")
    fake_agy.chmod(0o755)
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("hello", encoding="utf-8")
    output_file = blocker / "child" / "out.md"
    env = os.environ.copy()
    env["AI_WORKERS_ANTIGRAVITY_BIN"] = str(fake_agy)
    proc = subprocess.run(
        [
            "bash",
            str(GEMINI_SH),
            "--broker",
            "--prompt-file",
            str(prompt_file),
            "--output-file",
            str(output_file),
            "--acceptance",
            "non-empty",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 75
    assert not output_file.exists()


def test_broker_provenance_failure_does_not_update_artifact(tmp_path: Path) -> None:
    fake_agy = tmp_path / "agy"
    fake_agy.write_text("#!/bin/sh\necho 'fresh output'\n", encoding="utf-8")
    fake_agy.chmod(0o755)
    prompt_file = tmp_path / "prompt.txt"
    prompt_file.write_text("hello", encoding="utf-8")
    output_file = tmp_path / "out.md"
    output_file.write_text("stale artifact\n", encoding="utf-8")
    provenance_file = tmp_path / "blocked.provenance.json"
    provenance_file.write_text("{}\n", encoding="utf-8")
    provenance_file.chmod(0o444)
    env = os.environ.copy()
    env["AI_WORKERS_ANTIGRAVITY_BIN"] = str(fake_agy)
    proc = subprocess.run(
        [
            "bash",
            str(GEMINI_SH),
            "--broker",
            "--prompt-file",
            str(prompt_file),
            "--output-file",
            str(output_file),
            "--provenance-file",
            str(provenance_file),
            "--acceptance",
            "non-empty",
        ],
        cwd=REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 77
    assert output_file.read_text(encoding="utf-8") == "stale artifact\n"

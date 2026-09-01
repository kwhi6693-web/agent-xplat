from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.verification import _platform_label, run_verification


def test_runtime_verification_never_calls_static_inference_verified(tmp_path: Path):
    (tmp_path / "README.md").write_text("echo ok\n", encoding="utf-8")
    result = run_verification(tmp_path, Config())
    assert result["status"] in {"INFERRED", "VERIFIED", "FAIL"}
    assert result["evidence_type"] in {"INFERRED", "RUNTIME"}
    assert result["status"] != "VERIFIED" or any(check["status"] == "VERIFIED" for check in result["checks"])


def test_explicit_safe_project_test_is_reported_as_runtime_evidence(tmp_path: Path):
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_ok.py").write_text("def test_ok():\n    assert 1 + 1 == 2\n", encoding="utf-8")
    result = run_verification(tmp_path, Config(), timeout=30)
    command_check = next(check for check in result["checks"] if check["name"] == "project-command")
    assert command_check["status"] == "VERIFIED"
    assert result["status"] == "VERIFIED"


def test_platform_label_uses_public_os_names():
    assert _platform_label("Darwin") == "macos"
    assert _platform_label("Windows") == "windows"

from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.engine import scan


def test_global_and_line_suppressions_remain_auditable(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text(
        "# agent-xplat-ignore AX-SHELL-001\nchmod +x scripts/run.sh\nexport FOO=bar\n",
        encoding="utf-8",
    )
    result = scan(tmp_path, Config(ignore=("AX-SHELL-003",)))
    ignored = [finding for finding in result.findings if finding.ignored]
    assert {finding.rule_id for finding in ignored} >= {"AX-SHELL-001", "AX-SHELL-003"}
    assert result.summary["ignored_findings"] >= 2
    assert result.scores["windows-powershell"].status != "BLOCKED"


def test_supported_target_with_blocker_is_contract_violation(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text("chmod +x scripts/run.sh\n", encoding="utf-8")
    config = Config(supported=("windows-powershell", "linux-bash"))
    result = scan(tmp_path, config)
    assert result.contract["status"] == "VIOLATION"
    assert result.contract["violations"][0]["target"] == "windows-powershell"
    assert result.contract["violations"][0]["declared"] == "supported"


def test_unused_line_suppression_is_reported_without_silently_disappearing(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text(
        "# agent-xplat-ignore AX-SHELL-001\necho portable\n",
        encoding="utf-8",
    )
    result = scan(tmp_path, Config())
    diagnostics = result.summary["suppression_diagnostics"]
    assert diagnostics == [{
        "path": "SKILL.md",
        "line": 1,
        "rule_id": "AX-SHELL-001",
        "message": "suppression marker did not match a finding",
    }]

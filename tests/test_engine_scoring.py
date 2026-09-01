from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.engine import scan


def test_scan_returns_deterministic_scores_and_matrix(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text("chmod +x scripts/run.sh\n", encoding="utf-8")
    first = scan(tmp_path, Config())
    second = scan(tmp_path, Config())
    assert len(first.findings) > 0
    assert [finding.fingerprint for finding in first.findings] == [finding.fingerprint for finding in second.findings]
    assert first.scores == second.scores
    assert set(first.scores) == {target.id for target in first.targets}
    assert first.scores["windows-powershell"].status == "BLOCKED"
    assert first.scores["linux-bash"].status == "PASS"


def test_repository_metadata_checks_respect_excludes(tmp_path: Path):
    excluded = tmp_path / "generated"
    excluded.mkdir()
    (excluded / "CON.txt").write_text("generated\n", encoding="utf-8")
    config = Config(exclude=("generated/**",))
    result = scan(tmp_path, config)
    assert not any(finding.rule_id == "AX-FS-007" for finding in result.findings)

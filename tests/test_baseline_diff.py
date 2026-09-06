from pathlib import Path

from agent_xplat.baseline import compare_baseline, baseline_document
from agent_xplat.config import Config
from agent_xplat.diff import compare_scans
from agent_xplat.engine import scan


def test_baseline_separates_new_existing_and_resolved_findings(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text("chmod +x scripts/run.sh\n", encoding="utf-8")
    first = scan(tmp_path, Config())
    base = baseline_document(first)
    (tmp_path / "SKILL.md").write_text("export FOO=bar\n", encoding="utf-8")
    second = scan(tmp_path, Config())
    comparison = compare_baseline(second, base)
    assert comparison["new_count"] >= 1
    assert comparison["resolved_count"] >= 1
    assert comparison["status"] == "REGRESSION"


def test_diff_compares_before_and_after_scores(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text("echo ok\n", encoding="utf-8")
    before = scan(tmp_path, Config())
    (tmp_path / "SKILL.md").write_text("chmod +x scripts/run.sh\n", encoding="utf-8")
    after = scan(tmp_path, Config())
    result = compare_scans(before, after)
    assert result["regression"] is True
    assert result["scores"]["windows-powershell"]["before"] == 100
    assert result["scores"]["windows-powershell"]["after"] < 100


def test_new_baseline_ignores_line_shift_but_counts_duplicate_occurrences(tmp_path):
    path = tmp_path / 'SKILL.md'
    path.write_text('chmod +x run.sh\n')
    base = baseline_document(scan(tmp_path, Config()))
    path.write_text('# Heading\n\nchmod +x run.sh\n')
    assert compare_baseline(scan(tmp_path, Config()), base)['new_count'] == 0
    path.write_text('chmod +x run.sh\nchmod +x run.sh\n')
    assert compare_baseline(scan(tmp_path, Config()), base)['new_count'] == 1


def test_legacy_baseline_still_matches(tmp_path):
    (tmp_path / 'SKILL.md').write_text('chmod +x run.sh\n')
    result = scan(tmp_path, Config())
    base = baseline_document(result)
    for item in base['findings']:
        del item['match_key']
    assert compare_baseline(result, base)['new_count'] == 0

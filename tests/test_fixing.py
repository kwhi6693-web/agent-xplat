from pathlib import Path

from agent_xplat.config import Config
from agent_xplat.engine import scan
from agent_xplat.fixing import apply_fixes, plan_fixes


def test_crlf_shebang_fix_is_deterministic_dry_run_safe_and_idempotent(tmp_path: Path):
    path = tmp_path / "run.sh"
    path.write_bytes(b"#!/usr/bin/env bash\r\necho ok\r\n")
    result = scan(tmp_path, Config())
    fixes = plan_fixes(result)
    assert [fix["rule_id"] for fix in fixes] == ["AX-FS-001"]
    before = path.read_bytes()
    dry = apply_fixes(tmp_path, fixes, dry_run=True)
    assert path.read_bytes() == before
    assert "-#!/usr/bin/env bash" in dry["diff"]
    applied = apply_fixes(tmp_path, fixes, dry_run=False)
    assert applied["applied"] == 1
    assert path.read_bytes() == b"#!/usr/bin/env bash\necho ok\n"
    second = apply_fixes(tmp_path, plan_fixes(scan(tmp_path, Config())), dry_run=False)
    assert second["applied"] == 0


def test_fix_engine_does_not_rewrite_blockers_without_a_proven_fix(tmp_path: Path):
    path = tmp_path / "SKILL.md"
    path.write_text("chmod +x scripts/run.sh\n", encoding="utf-8")
    result = scan(tmp_path, Config())
    assert plan_fixes(result) == []

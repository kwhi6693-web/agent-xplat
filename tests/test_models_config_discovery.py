from pathlib import Path

import pytest

from agent_xplat.config import ConfigError, load_config
from agent_xplat.discovery import discover_files
from agent_xplat.environments import TARGETS, target_by_id
from agent_xplat.models import SourceFile


def test_target_matrix_keeps_os_shell_and_runtime_independent():
    assert len(TARGETS) == 8
    assert target_by_id("windows-powershell").os == "windows"
    assert target_by_id("windows-powershell").shell == "powershell"
    assert target_by_id("windows-powershell").runtime == "native"
    assert target_by_id("linux-zsh").os == "linux"
    assert target_by_id("linux-zsh").shell == "zsh"


def test_config_loader_validates_documented_schema(tmp_path: Path):
    (tmp_path / ".agent-xplat.yml").write_text(
        """targets:\n  - windows-powershell\n  - linux-bash\nexclude:\n  - vendor/**\nignore:\n  - AX-SHELL-001\nminimum_score: 85\nfail_on:\n  - BLOCKER\nrequirements:\n  python: \">=3.11\"\n""",
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert config.targets == ("windows-powershell", "linux-bash")
    assert "vendor/**" in config.exclude
    assert config.minimum_score == 85
    assert config.requirements["python"] == ">=3.11"


def test_config_loader_rejects_unknown_target(tmp_path: Path):
    (tmp_path / ".agent-xplat.yml").write_text("targets:\n  - solaris-ksh\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="unknown target"):
        load_config(tmp_path)


def test_config_loader_accepts_optional_agent_xplat_wrapper_and_validates_verification(tmp_path: Path):
    (tmp_path / ".agent-xplat.yml").write_text(
        """agent-xplat:
  targets:
    - linux-bash
  verification:
    command: python -m pytest -q
    timeout: 30
""",
        encoding="utf-8",
    )
    config = load_config(tmp_path)
    assert config.targets == ("linux-bash",)
    assert config.verification["timeout"] == 30


def test_config_loader_rejects_contract_targets_outside_scan_targets(tmp_path: Path):
    (tmp_path / ".agent-xplat.yml").write_text(
        "targets:\n  - linux-bash\nsupported:\n  - windows-powershell\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="included in targets"):
        load_config(tmp_path)


def test_config_loader_rejects_root_wrapper_key_collision(tmp_path: Path):
    (tmp_path / ".agent-xplat.yml").write_text(
        "minimum_score: 80\nagent-xplat:\n  minimum_score: 90\n",
        encoding="utf-8",
    )
    with pytest.raises(ConfigError, match="duplicated between root and agent-xplat"):
        load_config(tmp_path)


def test_config_loader_rejects_unknown_ignore_rule_and_duplicate_key(tmp_path: Path):
    (tmp_path / ".agent-xplat.yml").write_text("ignore:\n  - AX-NOT-REGISTERED\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="unknown ignore rule"):
        load_config(tmp_path)
    (tmp_path / ".agent-xplat.yml").write_text("minimum_score: 80\nminimum_score: 90\n", encoding="utf-8")
    with pytest.raises(ConfigError, match="duplicate configuration key"):
        load_config(tmp_path)


def test_discovery_is_deterministic_bounded_and_excludes_generated_dirs(tmp_path: Path):
    (tmp_path / "SKILL.md").write_text("# Skill\n", encoding="utf-8")
    (tmp_path / ".github").mkdir()
    (tmp_path / ".github" / "copilot-instructions.md").write_text("Use bash\n", encoding="utf-8")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "ignored.js").write_text("chmod +x x\n", encoding="utf-8")
    (tmp_path / "image.bin").write_bytes(b"\x00\x01\x02")
    first = discover_files(tmp_path, load_config(tmp_path))
    second = discover_files(tmp_path, load_config(tmp_path))
    assert [item.relative_path for item in first] == [item.relative_path for item in second]
    assert [item.relative_path for item in first] == [".github/copilot-instructions.md", "SKILL.md"]
    assert all(isinstance(item, SourceFile) for item in first)


def test_discovery_includes_javascript_and_typescript_dialect_extensions(tmp_path: Path):
    for name in ("view.jsx", "module.mts", "module.cts", "view.tsx"):
        (tmp_path / name).write_text("export const value = 1;\n", encoding="utf-8")
    discovered = {item.relative_path for item in discover_files(tmp_path, load_config(tmp_path))}
    assert {"view.jsx", "module.mts", "module.cts", "view.tsx"}.issubset(discovered)

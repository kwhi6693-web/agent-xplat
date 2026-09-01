"""Project initialization artifacts."""

from __future__ import annotations

from pathlib import Path


DEFAULT_CONFIG = """# agent-xplat configuration
targets:
  - windows-powershell
  - windows-git-bash
  - windows-wsl
  - macos-zsh
  - macos-bash
  - linux-bash
  - linux-zsh
exclude:
  - node_modules/**
  - vendor/**
  - tests/fixtures/**
ignore: []
minimum_score: 85
fail_on:
  - BLOCKER
  - ERROR
"""


CI_WORKFLOW = """name: agent-xplat

on:
  push:
  pull_request:

permissions:
  contents: read
  security-events: write

jobs:
  portability:
    name: ${{ matrix.os }}
    runs-on: ${{ matrix.os }}
    strategy:
      fail-fast: false
      matrix:
        os: [windows-latest, macos-latest, ubuntu-latest]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install project
        run: python -m pip install -e ".[dev]"
      - name: Tests
        run: python -m pytest -q
      - name: Static portability scan
        id: static_scan
        continue-on-error: true
        run: python -m agent_xplat scan . --format json --output agent-xplat-scan.json
      - name: Controlled runtime verification
        id: runtime_verification
        continue-on-error: true
        run: python -m agent_xplat test . --format json --output agent-xplat-verification.json
      - name: Markdown report
        if: always()
        run: python -m agent_xplat report . --output agent-xplat-report.md
      - name: Upload SARIF and reports
        if: always()
        run: python -m agent_xplat scan . --format sarif --output agent-xplat.sarif
      - name: Upload artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: agent-xplat-${{ matrix.os }}
          path: |
            agent-xplat-scan.json
            agent-xplat-verification.json
            agent-xplat-report.md
            agent-xplat.sarif
      - name: Upload SARIF to code scanning
        if: always()
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: agent-xplat.sarif
      - name: Enforce static portability gate
        if: always() && steps.static_scan.outcome == 'failure'
        run: exit 1
      - name: Enforce runtime verification gate
        if: always() && steps.runtime_verification.outcome == 'failure'
        run: exit 1
"""


def write_init(root: Path, force: bool = False) -> Path:
    path = Path(root) / ".agent-xplat.yml"
    if path.exists() and not force:
        raise FileExistsError(f"configuration already exists: {path}")
    path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    return path


def write_ci(root: Path, force: bool = False) -> Path:
    path = Path(root) / ".github" / "workflows" / "agent-xplat.yml"
    if path.exists() and not force:
        raise FileExistsError(f"workflow already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(CI_WORKFLOW, encoding="utf-8")
    return path


def badge_svg(static_checked: bool = True, runtime_verified: bool = False) -> str:
    if runtime_verified:
        label, value, color = "Cross-OS Verified", "Windows ✓ · macOS ✓ · Linux ✓", "#2ea44f"
    elif static_checked:
        label, value, color = "Static Checked", "Inference only", "#6f42c1"
    else:
        label, value, color = "Cross-OS", "Not checked", "#6a737d"
    width = max(260, 115 + len(value) * 7)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="20" role="img" aria-label="{label}: {value}"><title>{label}: {value}</title><rect width="115" height="20" fill="#24292e"/><rect x="115" width="{width - 115}" height="20" fill="{color}"/><text x="57" y="14" fill="#fff" font-family="Verdana,sans-serif" font-size="11" text-anchor="middle">{label}</text><text x="{115 + (width - 115) / 2}" y="14" fill="#fff" font-family="Verdana,sans-serif" font-size="11" text-anchor="middle">{value}</text></svg>\n'''


def write_badge(root: Path, runtime_verified: bool = False) -> Path:
    path = Path(root) / "agent-xplat-badge.svg"
    path.write_text(badge_svg(True, runtime_verified), encoding="utf-8")
    return path

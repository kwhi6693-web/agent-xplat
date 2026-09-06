"""Project initialization artifacts."""

from __future__ import annotations

from pathlib import Path
import re

from . import __version__


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


CI_WORKFLOW = r"""name: Agent workflow portability

on:
  push:
  pull_request:

permissions:
  contents: read

jobs:
  static-portability:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install the scanner (not the scanned project)
        run: python -I -m pip install 'TOOL_SPEC'
      - uses: actions/checkout@v4
        with:
          path: target
          fetch-depth: 0
          persist-credentials: false
      - name: Scan and preserve gate outcome
        id: scan
        shell: bash
        env:
          BASE_SHA: ${{ github.event.pull_request.base.sha }}
        run: |
          mkdir -p reports
          args=(target --baseline-only)
          if [[ -n "$BASE_SHA" ]]; then
            args+=(--diff "$BASE_SHA")
          fi
          status=0
          for format in json markdown sarif; do
            code=0
            python -I -m agent_xplat scan "${args[@]}" --format "$format" --output "reports/scan.$format" || code=$?
            if (( code > status )); then status=$code; fi
          done
          echo "exit_code=$status" >> "$GITHUB_OUTPUT"
      - name: Publish readable summary
        if: always()
        shell: bash
        run: |
          if [[ -f reports/scan.markdown ]]; then
            head -c 900000 reports/scan.markdown >> "$GITHUB_STEP_SUMMARY"
            printf '\n\nFull reports are available in the workflow artifacts.\n' >> "$GITHUB_STEP_SUMMARY"
          fi
      - uses: actions/upload-artifact@v4
        if: always()
        with:
          name: agent-xplat-static-reports
          path: reports/
          if-no-files-found: warn
      - name: Enforce portability gate
        if: always()
        env:
          SCAN_EXIT: ${{ steps.scan.outputs.exit_code }}
        run: |
          case "$SCAN_EXIT" in
            0) exit 0 ;;
            1|2|3) exit "$SCAN_EXIT" ;;
            *) echo 'Scanner did not complete'; exit 3 ;;
          esac
"""



def write_init(root: Path, force: bool = False) -> Path:
    path = Path(root) / ".agent-xplat.yml"
    if path.exists() and not force:
        raise FileExistsError(f"configuration already exists: {path}")
    path.write_text(DEFAULT_CONFIG, encoding="utf-8")
    return path


def write_ci(root: Path, force: bool = False, tool_ref: str | None = None) -> Path:
    path = Path(root) / ".github" / "workflows" / "agent-xplat.yml"
    if path.exists() and not force:
        raise FileExistsError(f"workflow already exists: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    if tool_ref is not None and not re.fullmatch(r"[0-9a-f]{40}", tool_ref):
        raise ValueError("tool-ref must be a full lowercase 40-character commit SHA")
    spec = (f"agent-xplat @ git+https://github.com/kwhi6693-web/agent-xplat.git@{tool_ref}"
            if tool_ref else f"agent-xplat=={__version__}")
    path.write_text(CI_WORKFLOW.replace("TOOL_SPEC", spec), encoding="utf-8")
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

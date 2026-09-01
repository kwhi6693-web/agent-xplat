"""Command-line entry point for agent-xplat."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from . import __version__
from .baseline import compare_baseline, load_baseline, write_baseline
from .config import ConfigError, load_config
from .diff import compare_scans, scan_git_reference
from .doctor import probe_capabilities, render_doctor
from .engine import scan
from .explain import explain_rule
from .init import write_badge, write_ci, write_init
from .reporting import render_json, render_markdown, render_sarif, render_terminal
from .terminal import emit


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="agent-xplat",
        description="Cross-OS Runtime Portability checker for AI Agent Workflows.",
    )
    parser.add_argument("--version", action="version", version=__version__)
    subparsers = parser.add_subparsers(dest="command", metavar="COMMAND")

    def add_scan_options(command_parser: argparse.ArgumentParser, path_default: str = ".") -> None:
        command_parser.add_argument("path", nargs="?", default=path_default, help="repository or workflow root")
        command_parser.add_argument("--format", choices=("terminal", "json", "sarif", "markdown"), default="terminal")
        command_parser.add_argument("--output", help="write output to a file instead of stdout")
        command_parser.add_argument("--diff", metavar="REF", help="compare with a Git reference")
        command_parser.add_argument("--baseline-only", action="store_true", help="fail only on new baseline findings")
        command_parser.add_argument("--no-baseline", action="store_true", help="do not load an existing baseline")
        command_parser.add_argument("--no-color", action="store_true", help="disable ANSI color")

    scan_parser = subparsers.add_parser("scan", help="infer cross-OS portability issues")
    add_scan_options(scan_parser)
    test_parser = subparsers.add_parser("test", help="run controlled runtime verification")
    test_parser.add_argument("path", nargs="?", default=".")
    test_parser.add_argument("--format", choices=("terminal", "json"), default="terminal")
    test_parser.add_argument("--output")
    test_parser.add_argument("--timeout", type=int, default=120)
    fix_parser = subparsers.add_parser("fix", help="plan and apply safe deterministic fixes")
    fix_parser.add_argument("path", nargs="?", default=".")
    fix_parser.add_argument("--dry-run", action="store_true")
    fix_parser.add_argument("--output")
    report_parser = subparsers.add_parser("report", help="write a Markdown portability report")
    report_parser.add_argument("path", nargs="?", default=".")
    report_parser.add_argument("--output")
    report_parser.add_argument("--no-baseline", action="store_true")
    explain_parser = subparsers.add_parser("explain", help="explain a portability rule")
    explain_parser.add_argument("rule_id")
    doctor_parser = subparsers.add_parser("doctor", help="probe local verification capabilities")
    doctor_parser.add_argument("--format", choices=("terminal", "json"), default="terminal")
    doctor_parser.add_argument("--output")
    baseline_parser = subparsers.add_parser("baseline", help="write the current findings baseline")
    baseline_parser.add_argument("path", nargs="?", default=".")
    baseline_parser.add_argument("--output")
    baseline_parser.add_argument("--force", action="store_true")
    init_parser = subparsers.add_parser("init", help="create a starter .agent-xplat.yml")
    init_parser.add_argument("path", nargs="?", default=".")
    init_parser.add_argument("--force", action="store_true")
    ci_parser = subparsers.add_parser("init-ci", help="create a three-OS GitHub Actions workflow")
    ci_parser.add_argument("path", nargs="?", default=".")
    ci_parser.add_argument("--force", action="store_true")
    badge_parser = subparsers.add_parser("badge", help="create a truthful static/runtime status badge")
    badge_parser.add_argument("path", nargs="?", default=".")
    badge_parser.add_argument("--runtime-verified", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = build_parser().parse_args(argv)
    except SystemExit as exc:
        # Keep the programmatic API useful for tests and embedding while
        # preserving argparse's normal command-line output and status.
        return int(exc.code or 0)
    if not args.command:
        build_parser().print_help()
        return 0
    try:
        return _dispatch(args)
    except (ConfigError, ValueError, FileNotFoundError, OSError) as exc:
        print(f"error: {exc}", file=__import__("sys").stderr)
        return 2
    except Exception as exc:  # pragma: no cover - defensive CLI boundary
        print(f"internal error: {exc}", file=__import__("sys").stderr)
        return 3


def _result_for(path: str, *, no_baseline: bool = False):
    root = Path(path).resolve()
    config = load_config(root)
    result = scan(root, config)
    baseline_path = root / ".agent-xplat-baseline.json"
    if not no_baseline:
        baseline = load_baseline(baseline_path)
        if baseline:
            result.baseline = compare_baseline(result, baseline)
    return root, config, result


def _scan_exit_code(result, config, *, baseline_only: bool = False, diff_data: dict | None = None) -> int:
    if diff_data and diff_data.get("regression"):
        return 1
    if result.contract.get("status") == "VIOLATION":
        return 1
    if baseline_only and result.baseline:
        return 1 if result.baseline.get("new_count", 0) else 0
    active = [finding for finding in result.active_findings if finding.severity.value in set(config.fail_on)]
    return 1 if active else 0


def _dispatch(args: argparse.Namespace) -> int:
    if args.command == "scan":
        root, config, result = _result_for(args.path, no_baseline=args.no_baseline)
        diff_data = None
        if args.diff:
            before = scan_git_reference(root, args.diff, config)
            diff_data = compare_scans(before, result)
            result.baseline = {"status": diff_data["status"], **diff_data}
        if args.format == "json":
            text = render_json(result)
        elif args.format == "sarif":
            text = render_sarif(result)
        elif args.format == "markdown":
            text = render_markdown(result)
        else:
            text = render_terminal(result, color=not args.no_color)
        emit(text, args.output)
        return _scan_exit_code(result, config, baseline_only=args.baseline_only, diff_data=diff_data)
    if args.command == "report":
        root, _, result = _result_for(args.path, no_baseline=args.no_baseline)
        output = args.output or str(root / "agent-xplat-report.md")
        emit(render_markdown(result), output)
        if not args.output:
            print(f"Wrote {output}")
        return _scan_exit_code(result, load_config(root))
    if args.command == "explain":
        text = explain_rule(args.rule_id)
        if text is None:
            print(f"unknown rule: {args.rule_id}", file=__import__("sys").stderr)
            return 2
        print(text, end="")
        return 0
    if args.command == "doctor":
        document = probe_capabilities()
        text = json.dumps(document, indent=2, sort_keys=True) + "\n" if args.format == "json" else render_doctor(document)
        emit(text, args.output)
        return 0
    if args.command == "baseline":
        root, _, result = _result_for(args.path, no_baseline=True)
        output = Path(args.output) if args.output else root / ".agent-xplat-baseline.json"
        if output.exists() and not args.force:
            raise FileExistsError(f"baseline already exists: {output}; use --force to replace it")
        write_baseline(output, result)
        print(f"Wrote baseline with {len(result.active_findings)} findings: {output}")
        return 0
    if args.command == "init":
        path = write_init(Path(args.path), force=args.force)
        print(f"Wrote {path}")
        return 0
    if args.command == "init-ci":
        path = write_ci(Path(args.path), force=args.force)
        print(f"Wrote {path}")
        return 0
    if args.command == "badge":
        if args.runtime_verified:
            evidence_path = Path(args.path).resolve() / "agent-xplat-verification.json"
            if not evidence_path.exists():
                raise ValueError("--runtime-verified requires agent-xplat-verification.json with three-OS evidence")
            try:
                evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                raise ValueError(f"invalid verification evidence: {evidence_path}") from exc
            verified_os = {str(value).lower() for value in evidence.get("verified_os", [])}
            if evidence.get("status") != "VERIFIED" or not {"windows", "macos", "linux"}.issubset(verified_os):
                raise ValueError("--runtime-verified requires VERIFIED evidence for windows, macos, and linux")
        path = write_badge(Path(args.path), runtime_verified=args.runtime_verified)
        print("Static Checked" if not args.runtime_verified else "Cross-OS Verified")
        print(f"Wrote {path}")
        return 0
    if args.command == "fix":
        from .fixing import apply_fixes, plan_fixes

        root, config, result = _result_for(args.path)
        fixes = plan_fixes(result)
        output = apply_fixes(root, fixes, dry_run=args.dry_run)
        emit(output["diff"], args.output)
        return 0
    if args.command == "test":
        from .verification import run_verification

        root = Path(args.path).resolve()
        config = load_config(root)
        verification = run_verification(root, config, timeout=int(config.verification.get("timeout", args.timeout)))
        text = json.dumps(verification, indent=2, sort_keys=True) + "\n" if args.format == "json" else _render_verification_terminal(verification)
        emit(text, args.output)
        return 0 if verification.get("status") in {"VERIFIED", "PASS"} else 1
    raise ValueError(f"unsupported command: {args.command}")


def _render_verification_terminal(document: dict) -> str:
    lines = ["Runtime Verification", "====================", f"Status: {document.get('status')}", f"Environment: {document.get('environment')}"]
    for item in document.get("checks", []):
        lines.append(f"- {item.get('name')}: {item.get('status')} — {item.get('observation')}")
    return "\n".join(lines) + "\n"

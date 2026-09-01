"""Static scan orchestration."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import re

from . import __version__
from .config import Config
from .contracts import evaluate_contract
from .discovery import _is_excluded, discover_files
from .environments import TARGETS
from .models import Finding, ScanResult
from .scoring import score_findings
from .suppression import apply_suppressions
from .rules import analyze_source


def scan(root: Path, config: Config | None = None) -> ScanResult:
    root = Path(root).resolve()
    config = config or Config()
    targets = tuple(target for target in TARGETS if target.id in config.targets)
    sources = discover_files(root, config)
    findings: list[Finding] = []
    for source in sources:
        findings.extend(analyze_source(source, config))
    # Filesystem metadata checks are intentionally performed separately from
    # content rules so ignored/generated directories do not affect analysis.
    findings.extend(_metadata_findings(root, targets, config))
    findings.sort(key=lambda finding: (finding.location.path, finding.location.line, finding.location.column, finding.rule_id, finding.fingerprint))
    findings, suppression_diagnostics = apply_suppressions(findings, {source.relative_path: source for source in sources}, config)
    scores = score_findings(findings, targets, config.minimum_score)
    contract = evaluate_contract(config, scores, findings)
    summary = {
        "files_scanned": len(sources),
        "findings": len([finding for finding in findings if not finding.ignored]),
        "ignored_findings": len([finding for finding in findings if finding.ignored]),
        "blockers": len([finding for finding in findings if not finding.ignored and finding.severity.value == "BLOCKER"]),
        "errors": len([finding for finding in findings if not finding.ignored and finding.severity.value == "ERROR"]),
        "warnings": len([finding for finding in findings if not finding.ignored and finding.severity.value == "WARNING"]),
        "infos": len([finding for finding in findings if not finding.ignored and finding.severity.value == "INFO"]),
        "contract_violations": len(contract.get("violations", [])),
        "suppression_diagnostics": suppression_diagnostics,
    }
    return ScanResult(
        # Reports must be portable and must not leak the scanner's machine path.
        root=".",
        targets=targets,
        findings=findings,
        scores=scores,
        source_files=tuple(source.relative_path for source in sources),
        summary=summary,
        contract=contract,
        scan_timestamp=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        tool_version=__version__,
    )


def _metadata_findings(root: Path, targets, config: Config) -> list[Finding]:
    """Create findings for repository-level filesystem portability hazards."""
    from .models import Confidence, Finding, Severity, SourceLocation
    from .rules.registry import get_rule

    findings: list[Finding] = []
    paths: dict[str, str] = {}
    try:
        candidates = sorted(root.rglob("*"), key=lambda item: (item.relative_to(root).as_posix().lower(), item.relative_to(root).as_posix()))
    except OSError:
        candidates = []
    for path in candidates:
        relative = path.relative_to(root).as_posix()
        if _is_excluded(relative, config):
            continue
        if path.is_symlink():
            spec = get_rule("AX-FS-002")
            if spec:
                findings.append(
                    Finding(
                        spec.rule_id, spec.title, spec.description,
                        SourceLocation(relative, 1, 1), spec.severity, spec.confidence,
                        tuple(target.id for target in targets),
                        "Repository contains a symlink or junction whose checkout behavior varies by target filesystem.",
                        spec.remediation, spec.examples, relative,
                        metadata={"severity_rationale": spec.severity_rationale, "confidence_rationale": spec.confidence_rationale},
                    )
                )
            continue
        if not path.is_file():
            continue
        lowered = relative.casefold()
        other = paths.get(lowered)
        if other and other != relative:
            spec = get_rule("AX-FS-005")
            if spec:
                findings.append(
                    Finding(
                        spec.rule_id, spec.title, spec.description,
                        SourceLocation(relative, 1, 1), spec.severity, spec.confidence,
                        tuple(target.id for target in targets),
                        f"Files {other} and {relative} collide on a case-insensitive filesystem.",
                        spec.remediation, spec.examples, relative,
                        metadata={"severity_rationale": spec.severity_rationale, "confidence_rationale": spec.confidence_rationale},
                    )
                )
        paths[lowered] = relative
        for component in Path(relative).parts:
            stem = component.split(".", 1)[0].upper()
            if re.search(r'[<>:"|?*]', component) or component.rstrip(" .") != component or stem in {"CON", "PRN", "AUX", "NUL", *(f"COM{i}" for i in range(1, 10)), *(f"LPT{i}" for i in range(1, 10))}:
                spec = get_rule("AX-FS-007")
                if spec:
                    findings.append(
                        Finding(
                            spec.rule_id, spec.title, spec.description,
                            SourceLocation(relative, 1, 1), spec.severity, spec.confidence,
                            tuple(target.id for target in targets),
                            f"Filename component {component!r} is not safe on Windows.",
                            spec.remediation, spec.examples, component,
                            metadata={"severity_rationale": spec.severity_rationale, "confidence_rationale": spec.confidence_rationale},
                        )
                    )
                break
        if any(ord(character) > 127 for character in relative):
            spec = get_rule("AX-FS-008")
            if spec:
                findings.append(
                    Finding(
                        spec.rule_id, spec.title, spec.description,
                        SourceLocation(relative, 1, 1), spec.severity, spec.confidence,
                        tuple(target.id for target in targets),
                        "Non-ASCII path requires explicit encoding and normalization coverage.",
                        spec.remediation, spec.examples, relative,
                        metadata={"severity_rationale": spec.severity_rationale, "confidence_rationale": spec.confidence_rationale},
                    )
                )
        if len(relative) > 240:
            spec = get_rule("AX-FS-006")
            if spec:
                findings.append(
                    Finding(
                        spec.rule_id, spec.title, spec.description,
                        SourceLocation(relative, 1, 1), spec.severity, spec.confidence,
                        tuple(target.id for target in targets),
                        "Path length is close to or above common Windows path limits.",
                        spec.remediation, spec.examples, relative,
                        metadata={"severity_rationale": spec.severity_rationale, "confidence_rationale": spec.confidence_rationale},
                    )
                )
    return findings

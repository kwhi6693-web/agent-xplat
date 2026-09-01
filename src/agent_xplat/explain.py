"""Rule explanation output."""

from __future__ import annotations

from .rules.registry import get_rule


def explain_rule(rule_id: str) -> str | None:
    spec = get_rule(rule_id.upper())
    if spec is None:
        return None
    lines = [
        f"{spec.rule_id}: {spec.title}",
        "",
        "Rule meaning",
        spec.description,
        "",
        "Why it matters",
        f"This assumption can fail in: {', '.join(spec.affected_environments)}.",
        "",
        "Affected platforms",
        ", ".join(spec.affected_environments),
        "",
        "Bad example",
        spec.examples[0],
        "",
        "Portable example",
        "Resolve the operation through an OS-neutral runtime API or an explicitly selected launcher.",
        "",
        "Suggested remediation",
        spec.remediation,
        "",
        "Severity rationale",
        spec.severity_rationale,
        "",
        "Confidence rationale",
        spec.confidence_rationale,
    ]
    return "\n".join(lines) + "\n"

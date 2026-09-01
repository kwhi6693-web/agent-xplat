# Project Rules

1. Static scan is offline, read-only, deterministic, and must not run repository code.
2. Every finding must identify a source location, rule ID, severity, confidence, target impact, reason, and remediation.
3. Low-confidence assumptions are never promoted to blockers without explicit rule evidence.
4. Configuration, baseline, and output schemas are versioned and backward-compatible within v1.0.
5. Traversal order, target order, finding order, fingerprints, score math, and machine-readable keys are stable.
6. A failed/unknown runtime probe is recorded as unavailable or unverified; it is not converted to PASS.
7. The scanner may inspect file metadata and parse source, but never imports or runs target code.
8. Generated reports never contain source contents beyond short snippets needed for a finding.
9. No network, AI API, telemetry, credential discovery, or upload path is included.
10. Any fix that cannot demonstrate deterministic behavior preservation remains a suggestion.

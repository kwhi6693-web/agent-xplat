# Improve consumer CI, baseline gating and evidence

The generated CI currently assumes the scanned repository is agent-xplat itself,
so external Skills cannot adopt it without installing/running their project.
The real-world study also exposed Markdown prose interpreted as shell commands
and existing findings blocking nominally new-only comparisons.

This change:
- installs only a pinned scanner in consumer CI, isolates imports from target
  source, and preserves readable summaries and JSON/SARIF artifacts before gating;
- respects fail_on for new findings, recognizes moved lines and counts duplicates;
- masks prose/non-shell Markdown examples for shell/quoting rules, and invokes
  each detector family once;
- adds source identity to reports and binds runtime badge assertions to source;
- documents a pinned ten-repository study and updates all three README languages.

Validation: baseline 88 tests; candidate 98 passing tests on Linux. Independent
wheel install and CLI smoke checks passed. Emitted workflow shell steps exercised
against an unrelated repository with target-import traps. No target code ran.

Limitations: manual review covered only 30 deliberately selected findings, not
all findings. Of 25 reviewed false positives, 22 were removed; 3 remain. Five
intentional platform designs remain reported with broad default targets. This
is a reviewed pilot candidate, not proven low-noise universal enforcement.

Version 1.0.2 is unreleased; preview workflows must use --tool-ref with the full
candidate commit SHA. Windows/macOS candidate CI and actual maintainer adoption
remain unverified. Keep this PR in draft; do not merge or publish automatically.

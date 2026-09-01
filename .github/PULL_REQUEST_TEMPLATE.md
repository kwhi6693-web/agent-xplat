## Portability change

Describe the cross-OS assumption this change affects.

## Evidence

- [ ] Positive and negative fixtures added or updated
- [ ] `python -m pytest -q`
- [ ] JSON/SARIF/CLI behavior checked when applicable
- [ ] Windows evidence recorded when applicable
- [ ] macOS/Linux evidence recorded when applicable

## Safety

- [ ] No target code executes during static tests
- [ ] No secrets, telemetry, uploads, or machine-specific paths added
- [ ] Autofix is deterministic, dry-run safe, and idempotent, or no autofix is provided

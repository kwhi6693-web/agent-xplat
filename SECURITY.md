# Security policy

## Scope

Security reports for agent-xplat itself are welcome. Portability findings in a scanned repository are analysis output and should be handled by that repository's maintainers.

## Safe operating model

Static commands read local source and metadata only. They do not execute target code, connect to a network, call an AI API, upload data, discover credentials, or emit telemetry. The explicit `test` command can run an allowlisted project test command with a bounded timeout; review the command and repository before using it.

## Reporting

Please report suspected vulnerabilities privately to the repository maintainers before opening a public issue. Include the affected version, a minimal reproduction, impact, and a safe mitigation. Do not attach real secrets or private source.

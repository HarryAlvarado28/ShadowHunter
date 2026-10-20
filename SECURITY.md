# 🔐 Security policy

ShadowHunter is an early-stage security workbench, not a production-certified audit platform.

## Report issues responsibly

For a potential security vulnerability, use GitHub's **private vulnerability reporting / security advisory** feature if enabled for this repository. Do not disclose working exploits, credentials, customer target details or sensitive logs in a public issue. If private reporting is unavailable, open a *non-sensitive* issue requesting a secure contact channel.

## Supported code

The active Python package is shadowhunterkit/. Historical prototypes in core/ and cmd/ are retained for reference and may not meet the same guarantees.

## Design requirements

- No implicit privilege escalation or unrequested third-party scans.
- Sanitize and validate inputs; do not pass them to a shell.
- Network operations must have timeouts and bounded responses.
- Workspaces and exports may contain sensitive material; protect and minimize stored data.
- Future active-assessment modules require documented authorization, scope, rate limits, stop controls and reproducible evidence.

No security guarantees are offered. Operate only with permission and review new modules before relying on them professionally.

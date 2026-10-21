# 🤝 Contributing to ShadowHunter

Thanks for helping build a focused, reliable security workbench.

## Before opening a PR

1. Discuss substantial additions in an issue: use case, target distribution, safety, dependencies and measurable value.
2. Prefer one **small, independently testable module** rather than a monolithic feature.
3. Keep the standard Python 3.11+ installation lightweight. Optional native tools must degrade gracefully.
4. Give every operation a clear command, explicit inputs, bounded timeouts, safe output and useful error messages.
5. Run offline tests, Python compilation and shell syntax checks before requesting review.
6. Do not include real credentials, private hostnames, personally identifying OSINT reports or live customer captures.

## Architecture

See [ARCHITECTURE.md](ARCHITECTURE.md) for module contracts, security boundaries and CI design.


- shadowhunterkit/cli.py: user interaction and reusable session commands.
- shadowhunterkit/modules.py: explicit module registry; do not execute unknown plugins automatically.
- shadowhunterkit/operations.py: bounded individual operations; split by domain as modules grow.
- shadowhunterkit/workspace.py: local context and persistence, with conservative permissions.
- tests/: regression tests that do not depend on public Internet connectivity.

A module that touches third-party infrastructure should document **authorization, allowable scope, rate limits, observability, cleanup and failure modes**. Avoid bypass mechanisms and intrusive defaults.

## PR expectations

Explain purpose, user-facing examples, affected modules, tests, compatibility and any new permissions. New language/runtime dependencies require an explicit justification and a fallback plan.

## Licensing

This project is distributed under the [MIT License](LICENSE). Contributions are submitted under the same license; ensure you have rights to contribute your work.

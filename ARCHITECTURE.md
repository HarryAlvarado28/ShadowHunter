# 🧱 ShadowHunter Architecture

> **Mission:** a lightweight, terminal-first workbench for reproducible, authorized security assessments. The Python installation runs without root, Go, Docker or a GPU.

## 1. Components

```text
Operator (Kali / Parrot / Ubuntu)
  │
  └── shadowhunter CLI (Python 3.11+)
       ├── Commands + accessible numbered menu
       ├── Explicit module catalog and dispatcher
       │    ├── System / hardware inventory (including compute.info)
       │    ├── Network and wireless visibility
       │    ├── Passive OSINT
       │    └── Local evidence SHA-256
       │          ├── Go worker (if installed)
       │          └── Python worker (built-in fallback)
       └── Named assessment sessions
            ├── Declared scope / target
            ├── Notes / operation history
            └── Local, private JSON persistence
```

- **Python** owns CLI, sessions, module orchestration and system-independent logic. Only standard-library dependencies are required to run.
- **Go** is used for measured, bounded concurrency and self-contained Linux binaries; `cmd/evidencehash/` provides the first example. No Go compiler is required at runtime.
- **Bash** is for the user-level install/uninstall and optional local builds, not for running arbitrary plugins.
- **GPU backends** are optional future *capabilities*, not a dependency. Hardware detection must precede any workload dispatch; unsupported devices fall back to CPU or report an unavailable capability. Never assume that a detected GPU supports compute.
- Additional languages must justify their maintenance, compiler, cross-platform and distribution costs with benchmarks. Keep modules independent of the CLI.

## 2. Execution contract

```text
user command → parse arguments → select explicit registered module
             → validate target and optional scope
             → check required capabilities / authorization for active tasks
             → bounded operation → structured result/error
             → local session history → JSON/terminal output
```

Current registration lives in `shadowhunterkit/modules.py`. The catalog uses stable IDs, categories, descriptions, target requirements and a callable. Modules return structured, serializable records; **no shell interpolation, automatic network scanning, unreviewed dynamic imports or module execution**.

**Extension direction:** define a small declarative manifest (`id`, `category`, `version`, `inputs`, `capabilities`, `permissions`, `artifacts`, `entrypoint`) and validate it before installing curated extensions. Load only explicitly enabled, locally installed providers. Treat external output as untrusted, limit it, and keep APIs versioned. No runtime downloads or silent dependency installation.

## 3. Assessment workspaces

A named session stores the target, declared scope, notes and bounded module history at `${XDG_STATE_HOME:-~/.local/state}/shadowhunter/sessions/<name>.json`. Files are created with private permissions; explicit exports are also private.

Reopening a session in another terminal **reloads disk context**; it does **not** share process RAM, terminal state or command history. Parallel updates to the same session are not yet transaction-safe; file locking is required before multiple writers can share one workspace safely. Treat sensitive client findings as confidential and do not put secrets in plain-text notes.

## 4. Module roadmap and safety boundaries

| Family | First-class interface | Safe operation / next milestone |
| --- | --- | --- |
| System | `system.info`, `compute.info` | Local runtime, CPU/RAM and GPU-adapter inventory; GPU computing unverified |
| Network | `network.interfaces` | Local counters; capture requires explicit permission and interface selection |
| Wireless | `wifi.status` | Cached, read-only WLAN metadata; no RF injection |
| OSINT | `osint.certificates` | Public certificate transparency, bounded HTTP |
| Evidence | `evidence.hash` | Local SHA-256, deterministic sorted records; chain-of-custody workflows later |
| Reporting | Planned | Assessment scope, findings, timestamps, evidence references, export |
| Credential audit | Planned | Offline, user-provided lab data; explicit authorization, rate limits, no default brute force |
| Wi-Fi assessment | Planned | Lab-only workflows: WPA2/WPA3 configuration, protocol and policy analysis; no unrestricted intrusion |
| Exploit research | Planned | Versioned, reviewed modules with target checks, opt-in and stop controls |
| Compute acceleration | Planned | Capability-based dispatch for reviewed workloads; CPU fallback and isolated optional GPU backends |

**Scope declarations are bookkeeping, not evidence of legal authorization.** Intrusive assessments require written rules of engagement, limits, logs and a stop mechanism. Preserve the distinction between Wi-Fi discovery, offline cryptographic evaluation, and attacks against a live access point.

Hashing a file for evidence is **not** password cracking or complete forensic preservation. Existing SHA-256 results detect byte changes; they cannot establish provenance by themselves.

## 5. Installing and packaging

**Contributor workflow:** `git clone -b cooking ... && cd ShadowHunter` then `bash install.sh`. The installer checks the system Python, installs only managed files in user-owned directories, and uses the prebuilt Go worker if present. It may compile the worker if a suitable Go compiler is *already* available; otherwise it uses the Python fallback. No `sudo`, `pip`, `Docker` or global shell aliases are required.

**Release workflow:** CI builds Linux AMD64 and ARM64 archives containing the Python package, install script and compiled Go worker; the operator unpacks an archive and runs `bash install.sh`. Artifacts are **not** a signed/public release until published and validated; reproducible build hashes and provenance are future release criteria.

## 6. CI and review

Exactly **one workflow/job** on pull requests and branch pushes:

1. Verify lint/static checks: Ruff, ShellCheck, `gofmt`, `go vet`.
2. Run **three Python and one Go** essential unit tests, plus smoke checks for the CLI.
3. Build independent Linux AMD64/ARM64 workers and package archives.

Use maintained GitHub-hosted Ubuntu, Node 24-based official actions, current stable Python/Go toolchains, minimal token permissions, and avoid untrusted scripts or floating third-party actions. A green CI verifies those checks only; it does not certify wireless attacks, real-world installation or absence of all bugs.

## 7. Authoritative references

- **NIST SP 800-115** — *Technical Guide to Information Security Testing and Assessment*, Scarfone, Souppaya, Cody & Orebaugh (2008): https://csrc.nist.gov/pubs/sp/800/115/final
- **OWASP WSTG** — *Web Security Testing Guide*: https://owasp.org/www-project-web-security-testing-guide/
- **NIST SP 800-63B** — *Digital Identity Guidelines: Authentication and Authenticator Management*: https://pages.nist.gov/800-63-4/sp800-63b.html
- **NIST SP 800-38 / 800-57** — cryptography guidance: https://csrc.nist.gov/publications/sp800
- **Go release policy:** https://go.dev/doc/devel/release
- **Python releases:** https://www.python.org/downloads/
- **GitHub Actions secure use:** https://docs.github.com/en/actions/security-for-github-actions/security-guides/security-hardening-for-github-actions

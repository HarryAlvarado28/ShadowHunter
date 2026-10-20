<div align="center">

# 🛡️ ShadowHunter
### Your terminal-first security workbench

**Modular OSINT · Network observability · Wireless visibility · Persistent workspaces**

[![CI](https://github.com/HarryAlvarado28/ShadowHunter/actions/workflows/ci.yml/badge.svg?branch=cooking)](https://github.com/HarryAlvarado28/ShadowHunter/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Linux](https://img.shields.io/badge/Linux-Kali%20%7C%20Parrot%20%7C%20Ubuntu-333333?logo=linux)
![Status](https://img.shields.io/badge/status-early%20preview-orange)

*A professional toolkit for learning, investigating, documenting and performing explicitly authorized assessments.*

</div>

---

## 🌑 Philosophy

ShadowHunter is **not another Metasploit**. It is a modular field kit: one recognizable terminal, clear tools for defined jobs, reusable context, and an extensible home for community contributions. Build the right tool for the task; do not bundle dependencies or privileged functions by default.

- 🧭 **Terminal-native:** interactive command loop **and** commands suitable for scripts.
- 🧰 **Small independent modules:** discover, run and extend without a monolith.
- 🗂️ **Persistent workspaces:** separate targets, notes, execution history and exports.
- 🪶 **Easy to install:** Python's standard library; no Docker, pip or sudo for basic usage.
- 🛡️ **Responsible by design:** harmless local inspection and passive public lookups first.
- 🧪 **Testable:** deterministic offline tests and a compatibility matrix.

## 🚀 Quick start

On **Kali Linux, Parrot OS, Ubuntu** or another Linux distribution with Python **3.11+**:

~~~bash
git clone https://github.com/HarryAlvarado28/ShadowHunter.git
cd ShadowHunter
git switch cooking
bash install.sh
shadowhunter
~~~

The installer copies only the new Python package into your **user** application directory and creates commands in ~/.local/bin. No root privileges or additional packages are required. If the command is not found, add ~/.local/bin to PATH or execute ~/.local/bin/shadowhunter.

**Try without installing:**

~~~bash
python3 -m shadowhunterkit
python3 -m shadowhunterkit modules
python3 -m shadowhunterkit run system.info
~~~

**Non-interactive workflow:**

~~~bash
shadowhunter session new mylab
shadowhunter --session mylab target set example.org
shadowhunter --session mylab scope add example.org
shadowhunter --session mylab run osint.certificates
shadowhunter --session mylab history
shadowhunter --session mylab session export mylab.session.json
~~~

Certificate queries require an internet connection. Public CT entries do not prove a listed hostname is live or under your control.

## 🧰 Available modules

| Category | Module | What it actually does | Status |
| --- | --- | --- | --- |
| 🖥️ System | system.info | OS, Python and local host information | ✅ Ready |
| 🌐 Network | network.interfaces | Local interfaces and Linux RX/TX byte counters | ✅ Ready |
| 📶 Wireless | wifi.status | Cached wireless listing using nmcli, without rescanning | ✅ Ready, optional nmcli |
| 🕵️ OSINT | osint.certificates | Public certificate-transparency names from crt.sh | ✅ Ready, requires internet |
| 🔍 Network audit | Port-scanning integration | Controlled scope, rate limits and evidence | 🧭 Planned |
| 📡 Wireless audit | Wi-Fi security assessment workflows | Explicitly authorized lab workflows | 🧭 Planned |
| 📚 Reporting | Evidence, findings, export formats | Reproducible assessment reports | 🧭 Planned |
| 🧩 Extensions | Third-party module manifest / API | Reviewable plugin system | 🧭 Planned |

This is a **scaffold, not a claim that all penetration-testing functions are implemented**. Existing experimental code in core/ and cmd/ is retained as legacy research material; it is **not** automatically loaded into the new menu or system-wide installation.

## 🖥️ Terminal experience

~~~text
╔════════════════════════════════════════╗
║  🛡️ SHADOWHUNTER  /  Security Workbench  ║
╚════════════════════════════════════════╝

shadowhunter:default > modules
shadowhunter:default > session new audit
shadowhunter:audit > target set example.org
shadowhunter:audit > scope add example.org
shadowhunter:audit > run osint.certificates
shadowhunter:audit > note add Reviewed public certificate names
shadowhunter:audit > history
shadowhunter:audit > tab
~~~

Use **1–4** for the quick-action menu, **m** for modules, **h** for help and **0** to exit. Run **help** for all commands. Use **doctor** to check Python, Linux integration and optional tools.

### 🗂️ Context across terminal tabs

Each session is a named *workspace*, not a daemon or a single memory address. Open a second terminal tab and run:

~~~bash
shadowhunter --session audit shell
~~~

You can also type **tab** in the interactive menu to get the correct command. Workspaces use private JSON files in:

~~~text
$XDG_STATE_HOME/shadowhunter/sessions/
# default: ~/.local/state/shadowhunter/sessions/
~~~

This stores declared scope, target names, notes and bounded module outputs/history with restrictive file permissions. **It does not share live RAM, environment variables or spawned processes** across tabs. Concurrent writes by two terminals to the *same session* are not yet transaction-safe: avoid simultaneous modifications until locking is implemented. Do not store passwords, tokens or sensitive client findings in plain-text notes; JSON exports should be handled as sensitive evidence.

## 🏗️ Project architecture

~~~text
ShadowHunter/
├── shadowhunterkit/           # Active application
│   ├── __main__.py            # python -m launcher
│   ├── cli.py                 # Menu, commands and session navigation
│   ├── modules.py             # Typed module catalog and dispatch
│   ├── operations.py          # Read-only OSINT/network/wireless tasks
│   └── workspace.py           # Private, versioned session storage
├── tests/                     # Offline regression tests
├── .github/workflows/ci.yml   # Multi-version Python checks
├── install.sh                 # Per-user installation (no sudo)
├── uninstall.sh               # Managed uninstallation
├── pyproject.toml             # Optional packaging metadata
├── core/                      # Legacy prototypes (not part of new CLI)
├── cmd/                       # Optional Go experiment (not required)
├── build.sh                   # Optional Go build only
└── README.md
~~~

**Language policy:** Python is the orchestration/core language. Go is optional for independently benchmarked performance-critical modules, not a mandatory dependency. As of October 2026, Python 3.15 and Go 1.27 are current stable release families; ShadowHunter supports older still-maintained Python versions to work with distribution packages. **Do not replace Kali/Parrot system Python just to install ShadowHunter.**

Optional Go prototype (only if Go is already present):

~~~bash
bash build.sh
./dist/shadowhunter-osint
~~~

The Go prototype is independent and not connected to the new Python module registry.

## 🧪 Quality and development

~~~bash
python3 -m unittest discover -s tests -v
python3 -m compileall -q shadowhunterkit
bash -n install.sh uninstall.sh build.sh
~~~

Development guidelines live in [CONTRIBUTING.md](CONTRIBUTING.md), with disclosure guidance in [SECURITY.md](SECURITY.md).

## 🧹 Uninstall

~~~bash
bash uninstall.sh
~~~

Removes the managed application and launcher only. **Sessions are preserved** to avoid deleting assessment notes. You can delete the session directory yourself when appropriate.

## ⚖️ Authorization, evidence and licensing

Operate only in authorized environments with a documented scope. A passive certificate lookup or locally cached Wi-Fi listing is **not a permit** to access another person's systems. Declaring a scope does not establish authorization. Future active modules must enforce explicit target scope, predictable rate limits, safe defaults, audit traces and stop controls.

The source is publicly visible, but **a public repository is not automatically an open-source license**. A repository license must be selected by the owner before redistribution/reuse permissions can be assumed. Contributions should follow the project's contribution and security guidelines.

---

<div align="center">

**🕵️ Build carefully. Assess responsibly. Document everything.**

*ShadowHunter — a toolkit that grows with the operator.*

</div>

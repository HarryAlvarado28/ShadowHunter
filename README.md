<div align="center">

# 🛡️ ShadowHunter
**A terminal-first, modular security workbench**

🕵️ OSINT · 🌐 Network · 📶 Wireless · 🧾 Evidence

[![CI](https://github.com/HarryAlvarado28/ShadowHunter/actions/workflows/ci.yml/badge.svg?branch=cooking)](https://github.com/HarryAlvarado28/ShadowHunter/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.15%20CI-3776AB?logo=python&logoColor=white)
![Go](https://img.shields.io/badge/Go-1.27.3-00ADD8?logo=go&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-green)

*Build carefully. Assess responsibly. Document everything.*

</div>

## 🌑 Philosophy

**ShadowHunter is not another Metasploit.** It's your professional field kit: simple at first, extensible by the community, with specialized modules for distinct security tasks. A clean Linux terminal comes first; optional native acceleration should never complicate installation.

## 🚀 Install on Kali, Parrot or Ubuntu

Requires only **Python 3.11+** already on the system. No Docker, `sudo` or `pip`.

```bash
git clone -b cooking https://github.com/HarryAlvarado28/ShadowHunter.git && cd ShadowHunter
bash install.sh
```

Launch with `shadowhunter` or `~/.local/bin/shadowhunter`. The installer automatically uses a compatible prebuilt Go worker if present, compiles one if Go is already installed, or falls back to Python. The application works without Go.

## 🧰 Available tools

| Module | Purpose |
| --- | --- |
| `system.info` | Local operating-system information |
| `compute.info` | CPU, RAM and GPU-adapter inventory (read-only) |
| `network.interfaces` | Local interfaces and traffic counters |
| `wifi.status` | Read-only cached WLAN status (`nmcli` when available) |
| `osint.certificates` | Public certificate-transparency research |
| `evidence.hash` | Local concurrent SHA-256 using Go or Python |

```text
shadowhunter > modules
shadowhunter > session new audit
shadowhunter:audit > scope add example.org
shadowhunter:audit > target set example.org
shadowhunter:audit > run osint.certificates
shadowhunter:audit > tab
```

Use `help` for commands or `doctor` for system capabilities. Sessions preserve context on disk across terminal tabs; they do **not** share live RAM.

## 🧱 Architecture

**Python:** CLI, modules, sessions, OSINT. **Go:** bounded concurrent work. **Bash:** installation and builds. Planned extensions include scoped network assessments, controlled Wi-Fi/credential-audit labs, reporting and optional GPU acceleration—not yet implemented.

➡️ **[Architecture and extension contracts](ARCHITECTURE.md)** · [Contributing](CONTRIBUTING.md) · [Security policy](SECURITY.md)

## 🧪 Quality

One focused CI workflow verifies lint/static checks, **3 Python + 1 Go core tests**, and Linux AMD64/ARM64 builds. The pipeline uses Python 3.15, Go 1.27.3 and maintained Node 24-based GitHub Actions. Its result is not a certification of every Linux environment.

## 📚 Foundations

- **Scarfone, Souppaya, Cody & Orebaugh**, [NIST SP 800-115](https://csrc.nist.gov/pubs/sp/800/115/final) — security testing and assessment.
- **OWASP**, [Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/) — structured testing.
- **NIST**, [SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html) — authentication security.

## ⚖️ License and use

[MIT License](LICENSE), © Harry Alvarado. Open for contributions under [CONTRIBUTING.md](CONTRIBUTING.md). Operate **only within written authorization and approved scope**. Never publish credentials, customer data or private evidence in issues or PRs.

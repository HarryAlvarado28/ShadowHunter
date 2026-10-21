<div align="center">

# 🛡️ ShadowHunter

### Your security workbench. One terminal. Endless possibilities.

**🕵️ Recon · 🌐 Network · 📡 Wireless · 🧾 Evidence · 🧩 Extensions**

[![CI](https://github.com/HarryAlvarado28/ShadowHunter/actions/workflows/ci.yml/badge.svg?branch=cooking)](https://github.com/HarryAlvarado28/ShadowHunter/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/Python-3.11%2B-3776AB?logo=python&logoColor=white)
![Go](https://img.shields.io/badge/Go-1.27-00ADD8?logo=go&logoColor=white)
[![MIT](https://img.shields.io/badge/License-MIT-22C55E)](LICENSE)
![Linux](https://img.shields.io/badge/Linux-Kali%20%7C%20Parrot%20%7C%20Ubuntu-30363D?logo=linux&logoColor=white)

**A lightweight, open-source toolkit for authorized security work.**

[🚀 Get started](#-quick-start) · [🧰 Toolkit](#-the-toolkit) · [🧩 Extensions](#-make-it-yours) · [🧱 Architecture](ARCHITECTURE.md)

</div>

---

> **🌑 The idea**
>
> **ShadowHunter is not another Metasploit.**
> It's a modular field kit: a focused tool for each task, a shared workspace for your findings, and room for the community to expand it—without a complicated setup.

## 🚀 Quick start

<kbd>1</kbd> **Get the source** &nbsp; <kbd>2</kbd> **Install**

```bash
git clone -b cooking https://github.com/HarryAlvarado28/ShadowHunter.git && cd ShadowHunter
bash install.sh
```

**Launch:** `shadowhunter` · **Check:** `shadowhunter doctor`

<sub>Designed for Kali, Parrot and Ubuntu with Python 3.11+. No Docker, root access or Go installation required. Native Go acceleration is optional.</sub>

## 🧰 The toolkit

| Area | Built-in capability | Module |
|:---|:---|:---|
| 🖥️ **System** | Host, CPU, memory & GPU inventory | `system.info`, `compute.info` |
| 🌐 **Network** | Interfaces & local traffic counters | `network.interfaces` |
| 📶 **Wireless** | Cached Wi-Fi network information | `wifi.status` |
| 🕵️ **OSINT** | Public certificate-transparency research | `osint.certificates` |
| 🧾 **Evidence** | Local SHA-256 hashing, Go or Python | `evidence.hash` |
| 🧩 **Extensions** | Opt-in third-party modules & local dictionaries | `module`, `dictionary` |

<details>
<summary><strong>💻 Peek inside the terminal</strong></summary>

```text
╔════════════════════════════════════════╗
║  🛡️ SHADOWHUNTER  /  Security Workbench  ║
╚════════════════════════════════════════╝
  [1] System  [2] Network  [3] Wi-Fi  [4] OSINT
  [m] Modules [h] Help     [0] Exit

shadowhunter:default > session new audit
shadowhunter:audit > target set example.org
shadowhunter:audit > run osint.certificates
shadowhunter:audit > tab
```

Sessions retain notes, targets and history across tabs—**not live process memory**.

</details>

## 🧩 Make it yours

Add a module, then run it. Extensions use an explicit manifest or a single recognized source file.

```text
module add /home/user/my-tools/example.py
module add /home/user/my-tools/network-check/
module add https://example.org/module.zip --sha256 EXPECTED_SHA256
modules
run external.example
```

Bring your **own dictionaries** without copying their contents:

```text
dictionary add /home/user/wordlists/common.txt common
dictionary add /home/user/wordlists/ collections
dictionary list
```

**Python, Bash, Go, Rust and executable binaries** can be registered. Source modules needing compilation are built at import time *only if the appropriate compiler is available*. Use `module list` and `module remove ID` to manage your catalog.

<sub>🔐 Remote bundles require HTTPS + SHA-256 verification. External modules run under your user account and are **not sandboxed**. Review third-party code before execution.</sub>

## 🧱 Built to grow

```text
             ShadowHunter CLI
                     │
          Sessions + Module Catalog
                     │
      Python core ─ Go workers ─ Extensions
                     │
         Local evidence & reports
```

**Next up:** structured findings, controlled wireless/credential audits, reviewed exploit modules and optional GPU compute backends. These advanced features are **planned, not yet implemented**.

**Project guides:** [🧱 Architecture](ARCHITECTURE.md) · [🤝 Contributing](CONTRIBUTING.md) · [🔐 Security](SECURITY.md)

## 🧪 Development

**One focused CI workflow:** 3 Python tests + 1 Go test → Python compilation → Linux AMD64/ARM64 builds → installation smoke test. **No linter gate.**

<details>
<summary><strong>📚 Technical foundations & responsible use</strong></summary>

- **NIST — Scarfone, Souppaya, Cody & Orebaugh:** [SP 800-115](https://csrc.nist.gov/pubs/sp/800/115/final), security testing.
- **OWASP:** [Web Security Testing Guide](https://owasp.org/www-project-web-security-testing-guide/).
- **NIST:** [SP 800-63B](https://pages.nist.gov/800-63-4/sp800-63b.html), authentication guidance.

Use ShadowHunter only where you have **documented authorization**. Never commit credentials or client evidence.

</details>

---

<div align="center">

**🕶️ Explore responsibly · Build together · Keep it lightweight**

Made for the terminal. Designed for the community.

**[MIT License](LICENSE)** · © Harry Alvarado

</div>

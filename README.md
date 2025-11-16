# TFTP Router Flasher

**TFTP Router Flasher** is a cross-platform command-line tool for flashing firmware to routers using the TFTP protocol. It is designed to assist in firmware recovery for routers that support TFTP-based rescue modes, such as many ASUS RT-series models.

This tool is a modern rewrite of the original [arescue](https://github.com/jnissin/arescue) script by [Joonas Nissinen](https://github.com/jnissin). It has been updated for Python 3, refactored for clarity, and packaged as a CLI utility with improved logging, interface detection, and dependency management.

---

## 📚 Contents

- [✨ Features](#-features)
- [📦 Installation](#-installation)
- [🛠️ Build Requirements](#️-build-requirements)
- [🚀 Usage](#-usage)
- [🖥️ Compatibility](#️-compatibility)
- [📄 License](#-license)
- [🤝 Contributing](#-contributing)
- [⚠️ Disclaimer](#-disclaimer)

---

## ✨ Features

- 🛠️ Automatically configures your network interface for rescue mode
- 📡 Scans IP ranges to detect routers in recovery mode
- 📤 Uploads firmware via TFTP using a Python client
- 🧾 Logs all activity to both console and file
- 🧪 Includes retry logic and fallback IP configurations
- 🧰 Packaged for easy installation and CLI use

---

## 📦 Installation

Clone the repository and install locally:

```bash
git clone https://github.com/vr-ski/tftp-router-flasher.git
cd tftp-router-flasher
pip install .
```

This will install the CLI command `tftp-router-flasher`, which you can run from your terminal.
> 💡 Make sure you're using `pip >= 21.3` to ensure proper support for `pyproject.toml` builds.

---

## 🛠️ Build Requirements

<details>
<summary>Click to expand Linux setup instructions</summary>

TFTP Router Flasher depends on Python packages like `psutil` that include native C extensions. To install successfully, your system must have:

- A C compiler (e.g. `gcc`)
- Python development headers (e.g. `Python.h`)
- Build tools (e.g. `make`, `binutils`)

### 🐧 Linux Setup Instructions

#### ✅ Debian / Ubuntu
```bash
sudo apt update
sudo apt install build-essential python3-dev
```

#### ✅ CentOS / RHEL / Fedora
```bash
sudo dnf groupinstall "Development Tools"
sudo dnf install python3-devel
```

#### ✅ Arch Linux
```bash
sudo pacman -S base-devel python
```

#### ✅ Void Linux
```bash
sudo xbps-install -S base-devel python3-devel
```

Once these are installed, you can run:

```bash
pip install .
```

Or, if you're using a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
pip install .
```

</details>

---

## 🚀 Usage

```bash
tftp-router-flasher --firmware /path/to/firmware.trx --interface eth0
```

### CLI Options

| Flag           | Description                                 | Default           |
|----------------|---------------------------------------------|-------------------|
| `--firmware`   | Path to the firmware file                   | *(required)*      |
| `--interface`  | Network interface to use                    | `en0`             |
| `--hostname`   | Router IP address                           | `192.168.1.1`     |
| `--timeout`    | TFTP upload timeout (seconds)              | `120`             |
| `--no-ping`      | Disable ping check. Useful for some models| `False`           |
| `--debug`      | Enable debug logging                        | `False`           |

---

## 🖥️ Compatibility

<details>
<summary>Click to view supported platforms</summary>

Tested on:

- ✅ Linux (Debian, Ubuntu, Arch)
- ✅ macOS
- ⚠️ Windows (not officially supported due to reliance on `ip` and `route` commands)

</details>

---

## 📄 License

This project is licensed under the [GPL-2.0 License](LICENSE).

> This project is inspired by [arescue](https://github.com/jnissin/arescue) by Joonas Nissinen, originally licensed under GPL-2.0.
> All original credit goes to the author.

---

## 🤝 Contributing

Pull requests are welcome! If you’ve tested this with other router models or added new features, feel free to open an issue or submit a PR.

---

## ⚠️ Disclaimer

This tool is provided as-is. Flashing firmware can permanently damage your device if done incorrectly. Use at your own risk.

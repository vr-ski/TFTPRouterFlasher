# 🤝 Contributing to TFTP Router Flasher

Thank you for your interest in contributing! Whether you're fixing bugs, improving documentation, testing on new hardware, or adding features — your help is welcome and appreciated.

---

## 📦 Project Scope

TFTP Router Flasher is a cross-platform CLI tool for flashing firmware to routers via TFTP, especially in recovery mode. It aims to be:

- Lightweight and dependency-minimal
- Compatible with Linux and macOS
- Easy to install and use
- Safe and transparent for users

---

## 🧰 How to Contribute

### 🐛 Report Bugs
- Search [issues](https://github.com/yourusername/tftp-router-flasher/issues) first to avoid duplicates
- Include:
  - OS and Python version
  - Router model (if relevant)
  - Steps to reproduce
  - Logs or error messages

### ✨ Suggest Features
- Open an issue with a clear description
- Explain the use case and why it’s valuable
- Bonus: suggest how it could be implemented

### 🛠️ Submit Code
1. Fork the repo
2. Create a new branch (`feature/my-feature` or `fix/my-bug`)
3. Make your changes
4. Run tests (if applicable)
5. Submit a pull request with a clear summary

### 📚 Improve Docs
- Typos, formatting, or clarity improvements are always welcome
- You can edit `README.md`, `CONTRIBUTING.md`, or add new docs under `/docs`

---

## 🧪 Development Setup

```bash
git clone https://github.com/vr-ski/tftp-router-flasher.git
cd tftp-router-flasher
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

To run the CLI:

```bash
tftp-router-flasher --help
```

To run tests (if available):

```bash
pytest tests/
```

---

## 🧼 Code Style

- Follow [PEP8](https://peps.python.org/pep-0008/)
- Use 4-space indentation
- Keep functions small and focused
- Prefer logging over print statements
- Use descriptive variable and function names

---

## 📄 License and Attribution

By contributing, you agree that your code will be released under the GPL-2.0 License.
This project is inspired by [arescue](https://github.com/jnissin/arescue) by Joonas Nissinen, originally licensed under GPL-2.0.

---

## 🙌 Thank You

Your contributions help keep this project alive and useful.
If you’ve tested this tool with a new router model or platform, please share your experience!

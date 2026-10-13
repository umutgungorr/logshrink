# Contributing to LogShrink

Thank you for your interest in contributing to **LogShrink**! We welcome community contributions, bug reports, and feature proposals that help keep terminal logs clean and developer debugging fast.

---

## 🛠️ Development Setup

LogShrink has **zero runtime dependencies** and uses Python 3.9+ standard library. Development dependencies (`pytest`, `pytest-cov`, `ruff`) are minimal.

### Prerequisites
- Python 3.9 or higher
- `uv` (recommended) or standard `pip` / `venv`
- `git`

### Quick Setup

```bash
# Clone the repository
git clone https://github.com/umutgungorr/logshrink.git
cd logshrink

# Create a virtual environment and install in editable mode with dev dependencies
python -m venv .venv

# On Linux / macOS:
source .venv/bin/activate

# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

# Install editable package and dev tools
pip install -e ".[dev]"
```

Alternatively with [`uv`](https://docs.astral.sh/uv/):
```bash
uv sync --all-extras
```

---

## 🧪 Running Tests & Quality Checks

Before submitting any Pull Request, ensure that all tests pass and code conforms to formatting and linting rules.

### Run Unit Tests
```bash
pytest
```

### Run Tests with Coverage
```bash
pytest --cov=src/logshrink --cov-report=term-missing
```

### Run Ruff Linter & Formatter
```bash
# Check linting rules
ruff check .

# Check formatting
ruff format --check .

# Auto-format and fix
ruff check --fix .
ruff format .
```

---

## 📐 Code Style & Guidelines

1. **Zero External Runtime Dependencies**: The core package runtime must strictly depend only on the Python standard library. Do not add third-party dependencies to `[project.dependencies]`.
2. **Type Annotations**: Use Python 3.9+ typing conventions (`from __future__ import annotations`).
3. **Cross-Platform Compatibility**: Code and CLI must run seamlessly on Linux, macOS, and Windows PowerShell/cmd.
4. **Resilient Streaming**: Never buffer unlimited lines into memory. Always process streams line-by-line and handle `BrokenPipeError` gracefully.

---

## 🔀 Submitting a Pull Request

1. Fork the repository and create your branch from `main`:
   ```bash
   git checkout -b feature/my-new-feature
   ```
2. Commit your changes with clear, descriptive commit messages:
   ```bash
   git commit -m "feat(detector): add support for Elixir stack traces"
   ```
3. Ensure all tests and linting pass locally.
4. Push your branch to GitHub and open a Pull Request against the `main` branch.
5. Provide a clear PR description explaining the problem and solution, including sample log snippets if applicable.

---

## 🐛 Reporting Issues

If you encounter unexpected behavior or have a feature suggestion:
1. Check the [Issues](https://github.com/umutgungorr/logshrink/issues) page to avoid duplicate reports.
2. Provide a minimal reproducible example (e.g. 5-10 lines of the noisy log input and the expected vs actual LogShrink output).
3. Include your operating system and Python version (`python --version`, `logshrink --version`).

---

## 📜 Code of Conduct

All contributors and participants are expected to adhere to the [Code of Conduct](CODE_OF_CONDUCT.md).

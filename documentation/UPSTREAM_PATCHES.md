# Upstream Hermes Agent Patches

This document tracks all patches applied to the local checkout of the official Hermes Agent (`vendor/hermes-agent`).

## Repository Identity & Base Commit
- **Upstream Repository:** `https://github.com/NousResearch/hermes-agent.git`
- **Fork Remote (`origin`):** `https://github.com/inbox-hasibur/hermes-agent.git`
- **Upstream Remote (`upstream`):** `https://github.com/NousResearch/hermes-agent.git`
- **Pinned Base Commit:** `2bd378ed1b8d6bf2192cb26e0a55ff3091e6bd19` (tag `v0.23.0`, 2026-11-05)
- **Local Branch:** `hummingbird`
- **Integration:** Installed in editable mode (`pip install -e vendor/hermes-agent`) into project virtualenv (`.venv`).

---

## Applied Patches

### Patch 1: Support Python 3.12 in `pyproject.toml` Core Dependencies
- **Commit SHA:** `b777adb791`
- **Author:** Hasibur Rahman
- **Files Modified:** `pyproject.toml`
- **Summary:** Update core dependency environment markers from `python_version >= '3.14'` to `python_version >= '3.11'`.
- **Justification & Root Cause:**
  - Upstream Hermes declares `requires-python = ">=3.11,<3.15"` in `pyproject.toml` metadata, indicating official support for Python 3.11 through 3.14.
  - However, all 47 core dependencies in the `dependencies = [...]` table had strict environment markers pinned to `; python_version >= '3.14'`.
  - When installed editable into a Python 3.12 virtual environment (e.g. Python 3.12.3 in Humming Bird Cockpit), `pip` skipped all runtime dependencies, resulting in runtime failures (`ModuleNotFoundError: No module named 'ruamel'`, `rich`, `psutil`, etc.).
  - Broadening the environment marker to `python_version >= '3.11'` allows `pip install -e vendor/hermes-agent` to install all necessary core dependencies directly into Python 3.12 environments while preserving upstream version pins.


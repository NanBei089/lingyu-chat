# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

`lingyu-chat` is an early-stage Python project (version 0.1.0) currently consisting only of PyCharm-generated scaffolding:

- `main.py` — sample entry point (`print_hi` demo), not real application code.
- `core/` — empty package (`__init__.py` only). Intended home for application code.
- No dependencies are declared in `pyproject.toml` (`dependencies = []`), even though `uv.lock` contains resolved packages from the environment.
- No tests, linter, formatter, or CI configuration exists yet. Do not assume commands for these; add them to this file if you introduce them.
- `.jbeval/datasets/` exists but is empty and unused.

Because there is essentially no implementation, treat new structure as a design decision rather than discovering existing conventions.

## Toolchain and commands

Requires Python >= 3.12 (the checked-in `.venv` runs Python 3.12.10). The project is managed with **uv** and a project-local `.venv`.

```powershell
uv sync                  # create/update .venv from pyproject.toml + uv.lock
uv add <package>         # add a runtime dependency (updates pyproject.toml and lock)
uv add --dev <package>   # add a dev dependency
uv run main.py           # run a script inside the project environment
uv lock --upgrade        # refresh the lockfile
```

Do not invoke the global `python`/`pip`; use `uv run` or `.venv\Scripts\python.exe` so imports resolve against the project environment.

## Notes

- Platform is Windows 11; primary shell is PowerShell. Use PowerShell syntax for commands (`$env:VAR`, backtick escaping) or the Bash tool for POSIX syntax — do not mix.
- `.venv/` is a local environment and is excluded from the project's IDE content roots; never edit files inside it.
- If adding a `src/` layout, note `.idea/lingyu-chat.iml` already declares `src/` as a source root.

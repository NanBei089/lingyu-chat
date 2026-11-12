# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project state

`lingyu-chat` is an early-stage Python project (version 0.1.0). Its intent-recognition code lives under `core/`; the rest is still PyCharm scaffolding:

- `main.py` — sample entry point (`print_hi` demo), not real application code.
- `core/` — application package: `intent_recognizer.py` (LLM-based intent recognition) and `prompts.py` (prompt text).
- `test/1.test_intent_recognizer.py` — a manual script (`if __name__ == "__main__":`) that recognizes a few sample inputs and prints the results. It is **not** a pytest suite: the module name starts with a digit and it defines no `test_*` functions, so pytest cannot collect it. Run it directly.
- pytest 9 is installed in `.venv` but is **not** declared in `pyproject.toml` or `uv.lock`, so `uv sync` will remove it. Run `uv add --dev pytest` before adding pytest-style tests.
- No linter, formatter, or CI configuration exists yet. Do not assume commands for these; add them to this file if you introduce them.
- `.jbeval/datasets/` exists but is empty and unused.

Because there is little implementation, treat new structure as a design decision rather than discovering existing conventions.

## Toolchain and commands

Requires Python >= 3.12 (the checked-in `.venv` runs Python 3.12.10). The project is managed with **uv** and a project-local `.venv`.

```powershell
uv sync                  # create/update .venv from pyproject.toml + uv.lock
uv add <package>         # add a runtime dependency (updates pyproject.toml and lock)
uv add --dev <package>   # add a dev dependency
uv run main.py           # run a script inside the project environment
uv lock --upgrade        # refresh the lockfile
uv run pytest -v         # collect/run pytest tests (only after pytest-style tests are added)
```

Run the manual test script from the project root — `test/` is `sys.path[0]`, so `import core` fails without the project root on `PYTHONPATH`:

```powershell
$env:PYTHONPATH = "."; uv run python "test/1.test_intent_recognizer.py"
```

The script calls the real Qwen model and needs `DASHSCOPE_API_KEY` set.

Do not invoke the global `python`/`pip`; use `uv run` or `.venv\Scripts\python.exe` so imports resolve against the project environment.

## Notes

- Platform is Windows 11; primary shell is PowerShell. Use PowerShell syntax for commands (`$env:VAR`, backtick escaping) or the Bash tool for POSIX syntax — do not mix.
- `.venv/` is a local environment and is excluded from the project's IDE content roots; never edit files inside it.
- If adding a `src/` layout, note `.idea/lingyu-chat.iml` already declares `src/` as a source root.

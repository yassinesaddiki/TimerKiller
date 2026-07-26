# CLAUDE.md

Guidance for Claude Code (or any future assistant) working in this repo.

## First step on any task
Read `CONTEXT.md` for the architecture overview, then read only the
`CONTEXT:` header comment at the top of the specific file(s) you need to
touch — not the whole file — to figure out if it's the right place to make
a change. Only read a file's full body once you've confirmed it's relevant.

## Project
TimerKiller — a Windows Pomodoro app that hard-blocks (kills) chosen
processes until a daily focus goal is met. Python + PySide6 + psutil,
packaged with PyInstaller. See `CONTEXT.md` for the full architecture map.

## Rules for this codebase

1. **Every file/class gets a `CONTEXT:` header.** When you create or
   substantially change a module or class, write/update a bullet-point
   docstring at the top: what it does, what depends on it, what it depends
   on. This is how future sessions stay cheap — read the header, not the file.

2. **Respect the layering** (see `CONTEXT.md` "Architecture"):
   `app.ui` → `app.core` / `app.enforcement` / `app.system` → nothing internal.
   Never import `app.ui` from `app.core` or `app.enforcement`. `app.main` is
   the only composition root.

3. **One responsibility per module (SRP).** Don't bolt a new feature onto an
   existing file just because it's convenient — add a new module in the
   package that matches its responsibility, and wire it in `app.main` or the
   relevant package `__init__.py`.

4. **The enforcer thread (`app.enforcement.blocker.start_enforcer`) must
   never crash or block indefinitely.** It runs independent of the UI; all
   exceptions inside its loop must be caught and logged, never re-raised.

5. **`app.core.state_manager` is the only module allowed to read/write
   `app/data/state.json`.** Everything else goes through its functions.

6. **Don't commit generated/runtime files**: `app/data/*.json`,
   `app/logs/*.log`, `build/`, `dist/`, `venv/`, `__pycache__/` are
   gitignored — keep it that way.

7. **Git workflow**: this repo is meant to be actively pushed/pulled going
   forward. Before making changes, check `git status`/`git log` for
   in-progress work. Commit logical, well-scoped changes with clear
   messages. Never force-push or rewrite history without explicit
   confirmation from the user.

## Useful docs already in the repo
- `README.md` — user-facing overview / install instructions.
- `.github/instructions/` — original build prompts and checklists used to
  scaffold this project (historical reference, not always current).

# Unify bulk Git commit command

## Metadata

- **Status:** [~] in progress
- **Created:** 2026-10-11T21:04:39+08:00
- **Modified:** 2026-10-11T21:24:11+08:00
- **Questionable:** false
- **Agents:** 1
- **Sessions:** 1
- **Commits:** none
- **Back references:** [Safe bulk Git workflows plan](safe-bulk-git-workflows.md), [approved specification](https://github.com/jokyv/scripts/issues/18)
- **Forward references:** none
- **Amendments:** 2026-10-11 — User approved merging push-all into auto-commit and migrating aliases. Removed duplicate CLI/function; migrated Bash and deprecated Nushell aliases. Validation and manual review passed; workflow scaffolding excluded per user.

## Purpose

Provide one bulk commit/push workflow with configured repositories as default and `--all` as the explicit `~/projects` scope.

## Problem

`--auto_commit --all` and `--push_all_dirs` scan the same repositories, but use separate implementations, commit messages, CLI options, and Bash aliases.

## Solution

Keep `--auto_commit` as the only bulk commit/push action. Preserve configured paths by default; use `--auto_commit --all` for all repositories under `~/projects`. Remove the separate push-all action. Point existing `gpusha` aliases at the canonical all-repositories form.

## Relevant files

### Existing files

- `bin/git_util.py` — CLI dispatch and duplicate push-all implementation.
- `tests/test_git_util.py` — existing bulk-operation behavior tests.
- `README.md` — CLI examples.
- `/home/jokyv/nixos-config/home/programs/bash.nix` — active Bash aliases.
- `/home/jokyv/nixos-config/home/programs/deprecated/nu.nix` — deprecated Nushell aliases; update stale option reference.

### New files

- None.

## Implementation phases

### Phase 1 — Consolidate CLI behavior and aliases

**Tasks**

1. [x] Adapt tests so all-repository commit/push and large-file skip behavior run through `--auto_commit --all`; verify the removed push-all option is no longer advertised or accepted.
2. [x] Remove the duplicate push-all function, summary, CLI option, and dispatch branch; retain auto-commit’s timestamped commit message and safety guard.
3. [x] Update `gpusha` in active Bash and deprecated Nushell configs to `--auto_commit --all`; remove duplicate push-all README examples.
4. [~] Run tests, format/lint hooks, Nix formatter on edited configs, inspect both repos' diffs, and commit only requested files.

**Testing strategy:** Extend existing CLI/system-boundary pytest tests; keep Git/fd subprocesses stubbed and verify oversized repositories are skipped while later repositories still process.

**Validation commands**

```bash
uv run --group dev pytest
uv run --group lint ruff check tests/test_git_util.py
uv run --group lint ruff format --check bin/git_util.py tests/test_git_util.py
uv run pre-commit run --files README.md bin/git_util.py tests/test_git_util.py
nixfmt --check /home/jokyv/nixos-config/home/programs/bash.nix /home/jokyv/nixos-config/home/programs/deprecated/nu.nix
```

## Validation

Complete when configured auto-commit and `--auto_commit --all` are the only documented modes, tests pass, legacy aliases no longer use `--push_all_dirs`, and both repository diffs exclude unrelated changes.

## Questions and answers

- **Canonical command?** `--auto_commit` with optional `--all`.
- **Legacy `gpusha` alias?** Keep it as a shortcut for `--auto_commit --all`.
- **Deprecated Nushell config?** Update its alias so it no longer references the removed flag.

## Out of scope

- `gpulla` and `gsa` aliases.
- Existing unrelated NixOS configuration changes.
- Closing the original GitHub issues.

## Notes

- Existing safe-bulk workflow implementation plan remains complete; this plan covers the later-approved command consolidation.
- Phase 1 red/green evidence: the legacy-option test first failed because `--push_all_dirs` was accepted; after removing the duplicate CLI path, `uv run --group dev pytest -q tests/test_git_util.py` passed (7 tests).
- The NixOS config repository already has an unrelated modification in `home/programs/noctalia/default.nix`; leave it untouched.
- Phase 1 migration: active Bash and deprecated Nushell `gpusha` aliases now call `--auto_commit --all`; README documents the single canonical path.
- Validation: 7 pytest tests passed; focused Ruff lint/format, full relevant pre-commit hooks, Nix formatting, CLI help check, and `git diff --check` passed. Full Ruff on `bin/git_util.py` retains 13 baseline violations noted in the prior plan.
- Review compared worktrees with `main`; no commits exist beyond either base. Parallel review agents were unavailable, so review was manual. Possible duplicate test stubs remain a judgment call; user chose to exclude workflow scaffolding from this feature commit. Scoped files are staged; awaiting commit confirmation.

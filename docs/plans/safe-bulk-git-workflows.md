# Safe bulk Git workflows for project repositories

## Metadata

- **Status:** [x] complete
- **Created:** 2026-10-11T19:06:15+08:00
- **Modified:** 2026-10-11T20:07:01+08:00
- **Questionable:** false
- **Agents:** 1
- **Sessions:** 1
- **Commits:** none
- **Back references:** [Git push all script](https://github.com/jokyv/scripts/issues/3), [auto_commit options](https://github.com/jokyv/scripts/issues/9)
- **Forward references:** [Approved specification](https://github.com/jokyv/scripts/issues/18)
- **Amendments:** 2026-10-11 — Started Phase 1; reorganized tasks into TDD vertical slices. Phase 1 completed with 3 passing tests. Phase 2 exposed and fixed push-all’s stale root; shared-root tests passed. Phase 3 added CRITICAL skip-and-continue guards to bulk commit/push. Phase 4 README and CLI help updated; validation narrowed after confirming existing Ruff baseline. All tests, focused Ruff checks, formatting, and pre-commit hooks passed.

## Purpose

Make bulk Git commands discover the user’s nested project repositories consistently and prevent oversized repositories from being committed or pushed without a prominent warning.

## Problem

The current bulk commands use different repository roots: push-all searches `~/repos`, while pull-all and status-all search the home directory. Auto-commit uses only configured paths. The user now keeps working repositories under `~/projects`, including nested repositories. Push-all also lacks the large-file guard used by auto-commit.

## Solution

Use `~/projects` as the shared discovery root for bulk repository commands, preserving existing exclusion patterns and `.git`-directory discovery. Add opt-in `--all` to auto-commit; without it, auto-commit continues to use configured paths. Require `--auto_commit` to activate the operation.

For bulk commit/push operations, detect files larger than 50 MB before modifying each repository. Print a terminal CRITICAL warning naming oversized file(s) and the skipped repository; skip that repository and continue processing the rest. Do not include worktrees or submodules, whose `.git` entries are files.

Keep changes in the active Git utility and its tests/documentation. Leave archived scripts and the unreferenced duplicate utility unchanged.

## Relevant files

### Existing files

- `bin/git_util.py` — CLI options, repository discovery, bulk auto-commit/push/pull/status behavior, and large-file checks.
- `README.md` — Git utility usage examples.
- `pyproject.toml` — pytest and Ruff development dependencies.
- `.pre-commit-config.yaml` — repository formatting and validation hooks.

### New files

- `tests/test_git_util.py` — behavior-focused tests for CLI selection, repository discovery, and large-file skip/continue behavior.

## Implementation phases

### Phase 1 — Opt-in all-repository auto-commit

Use the CLI as the public seam and stub subprocess calls at the system boundary. Each behavior test is written first, run red, then implemented and rerun green before moving to the next task.

**Tasks**

1. [x] Verify `--auto_commit --all` discovers and processes nested repositories under `~/projects`.
2. [x] Verify `--auto_commit` without `--all` still processes only configured paths.
3. [x] Verify `--all` alone does not trigger auto-commit.

**Testing strategy:** Use a temporary nested project tree; assert observable command working directories and commit/push behavior. Stub external `fd`/Git execution without mocking internal helpers.

**Validation commands**

```bash
uv run --group dev pytest tests/test_git_util.py
```

### Phase 2 — Consistent project-root discovery

Change active bulk discovery commands to use the same `~/projects` root while preserving exclusions and current `.git`-directory matching.

**Tasks**

1. [x] Add a behavior test showing push-all, pull-all, and status-all discover under `~/projects`, including nested repositories.
2. [x] Update those commands to share the project root; retain exclusions and ignore `.git` files, worktrees, and submodules.

**Testing strategy:** Run the behavior test red before changing command roots, then green. Assert discoveries through command working directories and user-visible results.

**Validation commands**

```bash
uv run --group dev pytest tests/test_git_util.py
```

### Phase 3 — CRITICAL large-file guard for bulk commits/pushes

Keep the existing 50 MB threshold. Ensure each oversized repository is reported and skipped independently, then continue processing later repositories.

**Tasks**

1. [x] Add a behavior test that auto-commit reports oversized files with a terminal CRITICAL warning and continues to the next repository; update the warning if test fails.
2. [x] Add a behavior test that push-all skips an oversized repository without commit/push, reports CRITICAL, and still pushes a later eligible repository; implement the guard and summary status.

**Testing strategy:** Use multiple temporary repositories and stub only external process execution. Assert warning text identifies the file/repository, skipped repositories receive no mutating Git commands, and later repositories still process.

**Validation commands**

```bash
uv run --group dev pytest tests/test_git_util.py
uv run --group lint ruff check tests/test_git_util.py
uv run --group lint ruff format --check bin/git_util.py tests/test_git_util.py
```

### Phase 4 — Documentation and final validation

Document the opt-in CLI behavior and shared project root, then run full validation.

**Tasks**

1. [x] Update README usage examples for configured auto-commit, `--auto_commit --all`, and bulk repository root behavior.
2. [x] Verify CLI help describes `--all` as an opt-in modifier that requires auto-commit.
3. [x] Run full tests, lint/format checks, and configured pre-commit hooks; resolve failures before completion.

**Testing strategy:** Check examples against actual CLI output; run the repository test suite and configured hooks.

**Validation commands**

```bash
uv run --group dev pytest
uv run --group lint ruff check tests/test_git_util.py
uv run --group lint ruff format --check bin/git_util.py tests/test_git_util.py
uv run pre-commit run --files README.md bin/git_util.py tests/test_git_util.py
```

## Validation

The plan is complete when every task is checked and all Phase 4 validation commands pass. Per-repository skip tests must demonstrate a visible CRITICAL warning, no commit/push for the oversized repository, and continued processing of later repositories.

## Questions and answers

- **What is the all-repositories root?** `~/projects`, searched recursively.
- **How is `--all` invoked?** Together with `--auto_commit`; configured paths remain the default.
- **Which repositories qualify?** Ordinary nested repositories with `.git` directories; worktrees and submodules are excluded.
- **What happens above 50 MB?** Print a terminal CRITICAL warning naming the file(s) and skipped repository, skip that repository, and continue.
- **Which scripts change?** Active Git utility only; archived scripts and the unreferenced duplicate remain untouched.

## Out of scope

- Git worktrees and submodules.
- Archived shell scripts and the unreferenced duplicate utility.
- Changes to per-repository Git behavior beyond repository selection and the specified bulk large-file guard.

## Notes

- Source specification: [Safe bulk Git workflows for project repositories](https://github.com/jokyv/scripts/issues/18).
- Existing requests: [#3](https://github.com/jokyv/scripts/issues/3) and [#9](https://github.com/jokyv/scripts/issues/9).
- The repository currently has no test suite; pytest is already available as a development dependency.
- Phase 1 task 1 red/green evidence: the new test first failed because `--all` was unrecognized; after adding CLI support, `uv run --group dev pytest -q tests/test_git_util.py` passed (1 test).
- Phase 1 task 2 evidence: `uv run --group dev pytest -q tests/test_git_util.py` passed (2 tests), confirming configured paths stay default.
- Phase 1 completion evidence: `uv run --group dev pytest -q tests/test_git_util.py` passed (3 tests), including `--all` alone printing help without invoking Git.
- Phase 2 red/green evidence: the shared-root test first failed because push-all searched `~/repos`; after updating push/pull/status roots, `uv run --group dev pytest -q tests/test_git_util.py` passed (4 tests).
- Phase 3 task 1 red/green evidence: the CRITICAL warning test first failed because output lacked the required literal severity; after updating the message, the focused pytest case passed.
- Phase 3 task 2 red/green evidence: the push-all test first showed oversized repositories were pushed without a warning; after adding the guard, the focused test passed.
- Phase 3 completion evidence: `uv run --group dev pytest -q tests/test_git_util.py` passed (6 tests), covering CRITICAL warnings, skipped repositories, and continued processing.
- Phase 4 task 1: README now documents configured versus all-repository auto-commit, the `~/projects` root, worktree/submodule exclusions, and CRITICAL skip behavior.
- Phase 4 task 2: `uv run --group dev python bin/git_util.py --help` confirms `--all` requires auto-commit and pull/push/status help names `~/projects`.
- Full Ruff on `bin/git_util.py` reports 13 violations also present in the committed baseline; left unchanged. Ruff lint on new tests and format checks pass.
- Final validation: all 6 pytest tests passed; Ruff test lint/format checks and pre-commit hooks passed for all changed files.

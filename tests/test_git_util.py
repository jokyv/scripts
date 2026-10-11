import importlib
import sys
from pathlib import Path
from subprocess import CompletedProcess
from unittest.mock import patch

import pytest

BIN = Path(__file__).resolve().parents[1] / "bin"
sys.path.insert(0, str(BIN))

with patch("python_sops.get_secret", return_value=None):
    git_util = importlib.import_module("git_util")


def test_auto_commit_all_processes_nested_project_repositories(monkeypatch, tmp_path):
    projects = tmp_path / "projects"
    repo = projects / "group" / "nested" / "repo"
    (repo / ".git").mkdir(parents=True)
    commands = []

    def run(cmd, capture_output=True, text=True, cwd=None, check=False):
        commands.append((cmd, cwd))
        if cmd[0] == "fd" and "-td" in cmd:
            base = Path(cwd)
            stdout = "\n".join(str(path.relative_to(base)) for path in base.rglob(".git") if path.is_dir())
        elif cmd[:2] == ["git", "status"] and "--porcelain" in cmd:
            stdout = " M tracked-file"
        else:
            stdout = ""
        return CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(git_util, "PROJECTS_PATH", projects)
    monkeypatch.setattr(git_util.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["git_util.py", "--auto_commit", "--all"])

    git_util.main()

    assert any(cmd[0] == "fd" and cwd == projects for cmd, cwd in commands)
    assert any(cmd[:2] == ["git", "push"] and cwd == repo for cmd, cwd in commands)
    assert any(
        cmd[:2] == ["git", "commit"] and cmd[-1].startswith("auto script backup at:") and cwd == repo
        for cmd, cwd in commands
    )


def test_auto_commit_without_all_uses_configured_paths(monkeypatch, tmp_path):
    repo = tmp_path / "configured-repo"
    repo.mkdir()
    commands = []

    def run(cmd, capture_output=True, text=True, cwd=None, check=False):
        commands.append((cmd, cwd))
        stdout = " M tracked-file" if cmd[:2] == ["git", "status"] and "--porcelain" in cmd else ""
        return CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(git_util.CONFIG, "paths", [repo])
    monkeypatch.setattr(git_util.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["git_util.py", "--auto_commit"])

    git_util.main()

    assert not any(cmd[0] == "fd" and "-td" in cmd for cmd, _ in commands)
    assert any(cmd[:2] == ["git", "push"] and cwd == repo for cmd, cwd in commands)


def test_all_without_auto_commit_only_prints_help(monkeypatch, capsys):
    commands = []

    def run(cmd, capture_output=True, text=True, cwd=None, check=False):
        commands.append((cmd, cwd))
        return CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(git_util.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["git_util.py", "--all"])

    git_util.main()

    assert "usage:" in capsys.readouterr().out.lower()
    assert commands == []


def test_bulk_discovery_commands_share_projects_root(monkeypatch, tmp_path):
    projects = tmp_path / "projects"
    repo = projects / "group" / "nested" / "repo"
    (repo / ".git").mkdir(parents=True)
    worktree = projects / "worktree"
    worktree.mkdir()
    (worktree / ".git").write_text("gitdir: ../repo/.git/worktrees/worktree\n")
    commands = []

    def run(cmd, capture_output=True, text=True, cwd=None, check=False):
        commands.append((cmd, cwd))
        if cmd[0] == "fd" and "-td" in cmd:
            base = Path(cwd)
            stdout = "\n".join(str(path.relative_to(base)) for path in base.rglob(".git") if path.is_dir())
        elif cmd[:2] == ["git", "pull"]:
            stdout = "Already up to date"
        else:
            stdout = ""
        return CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(git_util, "HOME", tmp_path)
    monkeypatch.setattr(git_util, "PROJECTS_PATH", projects)
    monkeypatch.setattr(git_util.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["git_util.py", "--auto_commit", "--all"])

    git_util.main()
    git_util.pull_all_git_dirs()
    git_util.status_all_git_dirs()

    discoveries = [(cmd, cwd) for cmd, cwd in commands if cmd[0] == "fd" and "-td" in cmd]
    assert len(discoveries) == 3
    assert all(cwd == projects for _, cwd in discoveries)
    assert all(cmd[-len(git_util.CONFIG.exclude_dirs) :] == git_util.CONFIG.exclude_dirs for cmd, _ in discoveries)
    git_workdirs = [cwd for cmd, cwd in commands if cmd[0] == "git"]
    assert repo in git_workdirs
    assert worktree not in git_workdirs


def test_auto_commit_critically_skips_oversized_repo_and_continues(monkeypatch, tmp_path, caplog):
    oversized = tmp_path / "projects" / "oversized"
    later = tmp_path / "projects" / "later"
    oversized.mkdir(parents=True)
    later.mkdir()
    commands = []

    def run(cmd, capture_output=True, text=True, cwd=None, check=False):
        commands.append((cmd, cwd))
        if cmd[0] == "fd" and "--size" in cmd:
            stdout = "oversized.bin" if cwd == oversized else ""
        elif cmd[:2] == ["git", "status"] and "--porcelain" in cmd:
            stdout = " M tracked-file"
        else:
            stdout = ""
        return CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(git_util.subprocess, "run", run)

    git_util.auto_commit([oversized, later])

    warning = caplog.text
    assert "CRITICAL" in warning
    assert str(oversized) in warning
    assert "oversized.bin" in warning
    assert "skipped" in warning.lower()
    assert not any(
        cmd[0] == "git" and cmd[1] in {"add", "commit", "push"} and cwd == oversized for cmd, cwd in commands
    )
    assert any(cmd[:2] == ["git", "push"] and cwd == later for cmd, cwd in commands)


def test_auto_commit_all_critically_skips_oversized_repo_and_continues(monkeypatch, tmp_path, caplog, capsys):
    projects = tmp_path / "projects"
    oversized = projects / "oversized"
    later = projects / "later"
    (oversized / ".git").mkdir(parents=True)
    (later / ".git").mkdir(parents=True)
    commands = []

    def run(cmd, capture_output=True, text=True, cwd=None, check=False):
        commands.append((cmd, cwd))
        if cmd[0] == "fd" and "-td" in cmd:
            base = Path(cwd)
            stdout = "\n".join(str(path.relative_to(base)) for path in base.rglob(".git") if path.is_dir())
        elif cmd[0] == "fd" and "--size" in cmd:
            stdout = "oversized.bin" if cwd == oversized else ""
        elif cmd[:2] == ["git", "status"] and "--porcelain" in cmd:
            stdout = " M tracked-file"
        else:
            stdout = ""
        return CompletedProcess(cmd, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(git_util, "PROJECTS_PATH", projects)
    monkeypatch.setattr(git_util.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["git_util.py", "--auto_commit", "--all"])

    git_util.main()

    warning = caplog.text
    assert "CRITICAL" in warning
    assert str(oversized) in warning
    assert "oversized.bin" in warning
    assert "skipped" in warning.lower()
    assert "skipped (large files)" in capsys.readouterr().out
    assert not any(
        cmd[0] == "git" and cmd[1] in {"add", "commit", "push"} and cwd == oversized for cmd, cwd in commands
    )
    assert any(cmd[:2] == ["git", "push"] and cwd == later for cmd, cwd in commands)


def test_push_all_option_is_rejected(monkeypatch, capsys, tmp_path):
    projects = tmp_path / "projects"
    projects.mkdir()

    def run(cmd, capture_output=True, text=True, cwd=None, check=False):
        return CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(git_util, "PROJECTS_PATH", projects)
    monkeypatch.setattr(git_util.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["git_util.py", "--push_all_dirs"])

    with pytest.raises(SystemExit) as error:
        git_util.main()

    assert error.value.code == 2
    assert "unrecognized arguments: --push_all_dirs" in capsys.readouterr().err

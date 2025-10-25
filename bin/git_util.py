#!/usr/bin/env python3

"""
Git utility functions for repository management.

A collection of utilities for managing Git repositories including automated
commits, status checks, and repository initialization.
"""

import argparse
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Tuple

import python_sops as ps
from messaging import display_message
from rich.console import Console
from rich.table import Table

# ===============================================
# Configuration & Constants
# ===============================================

HOME = Path.home()
FILE_SIZE_LIMIT = 50  # in MB


@dataclass
class GitConfig:
    """
    Configuration for git utility operations.

    Attributes
    ----------
    paths : List[Path]
        List of paths to monitor for auto-commits
    exclude_dirs : List[str]
        Directory patterns to exclude from searches
    file_size_limit : int
        Maximum file size in MB before warning

    """

    paths: List[Path] = None
    exclude_dirs: List[str] = None
    file_size_limit: int = FILE_SIZE_LIMIT

    def __post_init__(self):
        if self.paths is None:
            notes_path = ps.get_secret("notes_path")
            self.paths = [
                HOME / notes_path,
                HOME / "pics" / "wallpapers",
            ]
        if self.exclude_dirs is None:
            self.exclude_dirs = [
                "-gE",
                ".local/share",
                "-gE",
                "helix/",
                "-gE",
                ".pyenv",
                "-gE",
                ".cache/",
                "-gE",
                ".cargo/",
            ]


CONFIG = GitConfig()
console = Console()


# ===============================================
# Helper Functions
# ===============================================


def run_command(
    cmd: List[str], cwd: Optional[Path] = None, capture_output: bool = True
) -> Tuple[int, str, str]:
    """
    Run a command and return exit code, stdout, stderr.

    Parameters
    ----------
    cmd : List[str]
        Command and arguments to execute
    cwd : Optional[Path], optional
        Working directory for command execution, by default None
    capture_output : bool, optional
        Whether to capture command output, by default True

    Returns
    -------
    Tuple[int, str, str]
        Exit code, stdout, and stderr from command execution

    """
    try:
        result = subprocess.run(
            cmd, capture_output=capture_output, text=True, cwd=cwd
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def check_large_files(path: Path, size_limit: int = FILE_SIZE_LIMIT) -> List[str]:
    """
    Check for files exceeding size limit in repository.

    Parameters
    ----------
    path : Path
        Repository path to check
    size_limit : int, optional
        Size limit in MB, by default FILE_SIZE_LIMIT

    Returns
    -------
    List[str]
        List of files exceeding size limit

    """
    exit_code, stdout, stderr = run_command(
        ["fd", "-H", "--size", f"+{size_limit}MB", "-gE", ".git"], cwd=path
    )
    return stdout.splitlines() if exit_code == 0 else []


def get_git_status(path: Path) -> int:
    """
    Get number of changed files in repository.

    Parameters
    ----------
    path : Path
        Repository path to check

    Returns
    -------
    int
        Number of files with changes

    """
    exit_code, stdout, stderr = run_command(
        ["git", "status", "--porcelain"], cwd=path
    )
    return len(stdout.splitlines()) if exit_code == 0 else 0


def find_git_directories(
    base_path: Path, exclude_patterns: List[str]
) -> List[Path]:
    """
    Find all git directories under base path.

    Parameters
    ----------
    base_path : Path
        Base directory to search from
    exclude_patterns : List[str]
        Patterns to exclude from search

    Returns
    -------
    List[Path]
        List of paths containing .git directories

    """
    exit_code, stdout, stderr = run_command(
        ["fd", "-td", "-HI", "-g", ".git", *exclude_patterns], cwd=base_path
    )

    if exit_code != 0:
        return []

    git_dirs = []
    for git_dir in stdout.splitlines():
        # Convert to Path and get parent directory (remove .git)
        full_path = base_path / git_dir
        repo_path = full_path.parent
        git_dirs.append(repo_path)

    return git_dirs


# ===============================================
# Main Functions
# ===============================================


def auto_commit(paths: Optional[List[Path]] = None) -> None:
    """
    Automatically commit and push changes in specified repositories.

    Skips commit if any files over size limit are detected in the repo.

    Parameters
    ----------
    paths : Optional[List[Path]], optional
        List of repository paths to check, by default uses CONFIG.paths

    """
    if paths is None:
        paths = CONFIG.paths

    results = []

    for path in paths:
        console.rule("[bold red]Repository checks")

        if not path.exists():
            display_message("failure", f"Path: {path} does not exist.")
            results.append({"path": str(path), "status": "not found"})
            continue

        # Check for large files
        display_message(
            "checking",
            f"Checking large files (>{CONFIG.file_size_limit}MB) in repo: {path}",
        )
        big_files = check_large_files(path, CONFIG.file_size_limit)

        if big_files:
            display_message(
                "warning",
                f"Files larger than {CONFIG.file_size_limit}MB detected, skipping commit",
            )
            for file in big_files:
                display_message("warning", f"Large file: {file}")
            results.append({"path": str(path), "status": "skipped (large files)"})
            continue

        display_message(
            "success",
            f"No Files larger than {CONFIG.file_size_limit}MB found. Continuing...",
        )

        # Check for changes
        display_message("checking", f"If any changes for repo: {path}")
        changes_count = get_git_status(path)

        if changes_count == 0:
            display_message("success", "Nothing to commit, moving on!")
            results.append({"path": str(path), "status": "no changes"})
            console.print("")
        else:
            # Perform git operations
            run_command(["git", "add", "."], cwd=path)
            commit_message = f"auto script backup at: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
            run_command(["git", "commit", "-q", "-m", commit_message], cwd=path)
            run_command(["git", "push", "-q"], cwd=path)

            display_message("success", "Found changes!")
            display_message(
                "success", "git add, git commit and git push performed"
            )
            results.append({"path": str(path), "status": "committed & pushed"})
            console.print("")

    # Display summary table
    _display_auto_commit_summary(results)


def _display_auto_commit_summary(results: List[dict]) -> None:
    """
    Display summary table of auto-commit results.

    Parameters
    ----------
    results : List[dict]
        List of result dictionaries with path and status

    """
    if not results:
        return

    console.print("\n")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Repository", style="dim", width=50)
    table.add_column("Status", justify="center")

    for result in results:
        status = result["status"]
        match status:
            case "committed & pushed":
                status_text = "[green]✓ committed & pushed[/green]"
            case "no changes":
                status_text = "[blue]○ no changes[/blue]"
            case "skipped (large files)":
                status_text = "[yellow]⚠ skipped (large files)[/yellow]"
            case "not found":
                status_text = "[red]✗ not found[/red]"
            case _:
                status_text = f"[dim]{status}[/dim]"

        table.add_row(result["path"], status_text)

    console.print(table)


def clean_up() -> None:
    """
    Clean up ignored files from git index.

    Removes files from index that should be ignored according to .gitignore,
    then commits and pushes the changes.

    """
    display_message("info", "Cleaning up ignored files from git index")

    # Remove the files from the index (not the actual files in the working copy)
    run_command(["git", "rm", "-r", "--cached", "."], capture_output=False)

    # Add these removals to the Staging Area
    run_command(["git", "add", "."], capture_output=False)

    # Commit them
    run_command(
        ["git", "commit", "-m", "Clean up ignored files"], capture_output=False
    )

    # Push
    run_command(["git", "push"], capture_output=False)

    display_message("success", "Cleanup completed and pushed")


def commit_workflow(commit_message: str) -> None:
    """
    Execute standard commit workflow with checks.

    Parameters
    ----------
    commit_message : str
        Commit message to use

    """
    display_message(
        "checking", f"if any file above {CONFIG.file_size_limit} MB exist"
    )

    # Get the path to the git folder
    exit_code, stdout, stderr = run_command(
        ["git", "rev-parse", "--show-toplevel"]
    )
    if exit_code != 0:
        display_message("error", "Not in a git repository")
        return

    dir_path = Path(stdout.strip())

    # Check if big files exist before committing
    big_files = check_large_files(dir_path, CONFIG.file_size_limit)

    if big_files:
        display_message(
            "warning", f"file(s) bigger than {CONFIG.file_size_limit}MB exist.."
        )
        display_message("warning", "delete or ignore the below file(s):")
        for file in big_files:
            console.print(f"  {file}")
        return

    display_message("success", "no big files found!")
    display_message("info", "proceeding with git add, commit, and push")

    # Git add everything
    run_command(["git", "add", "-A"], capture_output=False)

    # Commit change with commit_message
    run_command(["git", "commit", "-q", "-m", commit_message], capture_output=False)

    # Git push
    run_command(["git", "push", "-q"], capture_output=False)

    # Check git status
    display_message("info", "below is the current git status of the repo")
    run_command(["git", "status", "-sb"], capture_output=False)


def init_template() -> None:
    """
    Initialize a git repository with basic .gitignore template.

    Creates a git repository and .gitignore file with common Python exclusions.
    Raises FileExistsError if repository already exists.

    Raises
    ------
    FileExistsError
        If .git directory already exists

    """
    try:
        # Check if a Git repository already exists
        if Path(".git").exists():
            raise FileExistsError(
                "Git repository already exists in this directory."
            )

        display_message("info", "Initializing git repository")

        # Initialize Git repository
        run_command(["git", "init"], capture_output=False)

        # Create .gitignore file
        gitignore_content = "*.csv\n*.pkl\n*.xlsx\n*.txt\n__pycache__\n"
        Path(".gitignore").write_text(gitignore_content)

        # Add .gitignore to staging area
        run_command(["git", "add", ".gitignore"], capture_output=False)

        # Commit changes
        run_command(
            [
                "git",
                "commit",
                "-m",
                "git init and git add - basic git ignore file",
            ],
            capture_output=False,
        )

        display_message("success", "Repository initialized with .gitignore")

    except FileExistsError as e:
        display_message("error", str(e))


def log_graph() -> None:
    """
    Display git log as a formatted graph.

    Shows last 10 commits with decorations and branch information.

    """
    git_log_command = [
        "git",
        "log",
        "--graph",
        "-10",
        "--abbrev-commit",
        "--decorate",
        "--format=format:%C(bold green)%h%C(reset) - %C(bold cyan)%aD%C(reset) %C(bold yellow)(%ar)%C(reset)%C(auto)%d%C(reset)%n%C(white)%s%C(reset) %C(dim white)- %an%C(reset)",
        "--all",
    ]
    run_command(git_log_command, capture_output=False)


def pull_all_git_dirs() -> None:
    """
    Pull updates for all git repositories under home directory.

    Finds all git directories and executes git pull for each.
    Excludes directories specified in CONFIG.exclude_dirs.

    """
    display_message("info", "Finding all git repositories")

    git_dirs = find_git_directories(HOME, CONFIG.exclude_dirs)

    if not git_dirs:
        display_message("warning", "No git repositories found")
        return

    display_message("info", f"Found {len(git_dirs)} repositories")

    results = []

    for repo_path in git_dirs:
        console.print("")
        console.rule("[bold red]Checking repo")

        display_message("checking", f"Pulling updates for: {repo_path}")

        exit_code, stdout, stderr = run_command(["git", "pull"], cwd=repo_path)

        if exit_code == 0:
            if "Already up to date" in stdout:
                status = "up to date"
            else:
                status = "updated"
        else:
            status = "error"

        results.append({"path": str(repo_path), "status": status})

    # Display summary
    _display_pull_summary(results)


def _display_pull_summary(results: List[dict]) -> None:
    """
    Display summary table of pull results.

    Parameters
    ----------
    results : List[dict]
        List of result dictionaries with path and status

    """
    if not results:
        return

    console.print("\n")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Repository", style="dim", width=50)
    table.add_column("Status", justify="center")

    for result in results:
        status = result["status"]
        match status:
            case "updated":
                status_text = "[green]✓ updated[/green]"
            case "up to date":
                status_text = "[blue]○ up to date[/blue]"
            case "error":
                status_text = "[red]✗ error[/red]"
            case _:
                status_text = f"[dim]{status}[/dim]"

        table.add_row(result["path"], status_text)

    console.print(table)


def push_all_git_dirs() -> None:
    """
    Push changes for all git repositories in repos directory.

    Finds all git directories under ~/repos and pushes any uncommitted changes
    with an auto-generated commit message.

    """
    repos_path = HOME / "repos"

    if not repos_path.exists():
        display_message("error", f"Repos directory not found: {repos_path}")
        return

    display_message("info", "Finding all git repositories in repos directory")

    git_dirs = find_git_directories(repos_path, CONFIG.exclude_dirs)

    if not git_dirs:
        display_message("warning", "No git repositories found")
        return

    display_message("info", f"Found {len(git_dirs)} repositories")

    results = []

    for repo_path in git_dirs:
        changes_count = get_git_status(repo_path)

        if changes_count > 0:
            console.print("")
            display_message("warning", f"{repo_path.name} repo needs a git commit")

            # Run git add, commit and push
            commit_message = "This is an auto generated git commit!"
            run_command(["git", "add", "."], cwd=repo_path)
            run_command(
                ["git", "commit", "-qm", commit_message], cwd=repo_path
            )
            run_command(["git", "push", "-q"], cwd=repo_path)

            display_message("success", "git auto commit was pushed!")
            results.append({"path": str(repo_path), "status": "committed & pushed"})
        else:
            results.append({"path": str(repo_path), "status": "no changes"})

    # Display summary
    _display_push_summary(results)


def _display_push_summary(results: List[dict]) -> None:
    """
    Display summary table of push results.

    Parameters
    ----------
    results : List[dict]
        List of result dictionaries with path and status

    """
    if not results:
        return

    console.print("\n")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Repository", style="dim", width=50)
    table.add_column("Status", justify="center")

    for result in results:
        status = result["status"]
        match status:
            case "committed & pushed":
                status_text = "[green]✓ committed & pushed[/green]"
            case "no changes":
                status_text = "[blue]○ no changes[/blue]"
            case _:
                status_text = f"[dim]{status}[/dim]"

        table.add_row(result["path"], status_text)

    console.print(table)


def status_all_git_dirs() -> bool:
    """
    Check all git directories for uncommitted changes.

    Returns
    -------
    bool
        True if any repository has uncommitted changes, False otherwise

    """
    display_message("info", "Checking status of all git repositories")

    git_dirs = find_git_directories(HOME, CONFIG.exclude_dirs)

    if not git_dirs:
        display_message("warning", "No git repositories found")
        return False

    display_message("info", f"Found {len(git_dirs)} repositories")

    results = []
    changes_exist = False

    for repo_path in git_dirs:
        changes_count = get_git_status(repo_path)

        if changes_count > 0:
            console.print("")
            display_message("warning", f"{repo_path.name} repo needs a git commit")
            run_command(["git", "status", "-sb"], cwd=repo_path, capture_output=False)
            changes_exist = True
            results.append(
                {"path": str(repo_path), "status": f"{changes_count} changes"}
            )
        else:
            results.append({"path": str(repo_path), "status": "clean"})

    # Display summary
    _display_status_summary(results)

    return changes_exist


def _display_status_summary(results: List[dict]) -> None:
    """
    Display summary table of status check results.

    Parameters
    ----------
    results : List[dict]
        List of result dictionaries with path and status

    """
    if not results:
        return

    console.print("\n")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Repository", style="dim", width=50)
    table.add_column("Status", justify="center")

    for result in results:
        status = result["status"]
        if status == "clean":
            status_text = "[green]✓ clean[/green]"
        else:
            status_text = f"[yellow]⚠ {status}[/yellow]"

        table.add_row(result["path"], status_text)

    console.print(table)


def create_and_push_gh_repo(repo_dir: str = ".") -> bool:
    """
    Create a private GitHub repository and push current branch.

    Creates a private GitHub repository from a specified directory,
    pushes the current branch (HEAD) from that directory, and opens
    the new repository page in the default web browser.

    Parameters
    ----------
    repo_dir : str, optional
        The path to the local directory to use as the source, by default "."

    Returns
    -------
    bool
        True if all steps completed successfully, False otherwise

    Raises
    ------
    FileNotFoundError
        If 'gh' or 'git' command is not found
    subprocess.CalledProcessError
        If any of the underlying shell commands fail

    """
    repo_path = Path(repo_dir)

    # Ensure the directory exists
    if not repo_path.is_dir():
        display_message("error", f"Directory not found: {repo_dir}")
        return False

    # Define the sequence of commands
    commands = [
        ["gh", "repo", "create", "--private", "--source=.", "--remote=origin"],
        ["git", "push", "-u", "origin", "HEAD"],
        ["gh", "browse"],
    ]

    current_step = ""
    try:
        # Step 1: Create GitHub repository
        current_step = "gh repo create"
        display_message("info", f"Creating GitHub repository in: {repo_path.absolute()}")

        exit_code, stdout, stderr = run_command(commands[0], cwd=repo_path)
        if exit_code != 0:
            display_message("error", f"Failed to create repository: {stderr}")
            return False

        display_message("success", "Repository created")
        if stdout:
            console.print(stdout.strip())

        # Step 2: Push the current branch
        current_step = "git push"
        display_message("info", "Pushing current branch to GitHub")

        exit_code, stdout, stderr = run_command(commands[1], cwd=repo_path)
        if exit_code != 0:
            display_message("error", f"Failed to push: {stderr}")
            return False

        display_message("success", "Branch pushed successfully")

        # Step 3: Open in browser
        current_step = "gh browse"
        display_message("info", "Opening repository in browser")

        exit_code, stdout, stderr = run_command(commands[2], cwd=repo_path)
        if exit_code != 0:
            display_message("warning", f"Could not open browser: {stderr}")
            # Don't return False here as the main operations succeeded

        display_message("success", "All steps completed successfully")
        return True

    except FileNotFoundError as e:
        display_message(
            "error",
            f"Command '{e.filename}' not found during step '{current_step}'",
        )
        display_message(
            "info",
            "Please ensure 'gh' and 'git' are installed and in your system's PATH",
        )
        return False
    except Exception as e:
        display_message(
            "error", f"An unexpected error occurred during step '{current_step}': {e}"
        )
        return False


# ===============================================
# Main Entry Point
# ===============================================


def main() -> None:
    """
    Main entry point for git utility CLI.

    Parses command line arguments and executes the requested git operation.

    """
    parser = argparse.ArgumentParser(
        prog="GIT Utility", description="Utility CLI for GIT custom commands"
    )

    parser.add_argument(
        "-cw", "--commit_workflow", action="store_true", help="Execute commit workflow"
    )
    parser.add_argument(
        "-ac", "--auto_commit", action="store_true", help="Auto-commit configured paths"
    )
    parser.add_argument(
        "-cu", "--clean_up", action="store_true", help="Clean up ignored files"
    )
    parser.add_argument(
        "-it", "--init_template", action="store_true", help="Initialize git repository with template"
    )
    parser.add_argument(
        "-lg", "--log_graph", action="store_true", help="Display git log graph"
    )
    parser.add_argument(
        "-pld", "--pull_all_dirs", action="store_true", help="Pull all git directories"
    )
    parser.add_argument(
        "-pud", "--push_all_dirs", action="store_true", help="Push all git directories in repos"
    )
    parser.add_argument(
        "-std", "--status_all_dirs", action="store_true", help="Check status of all git directories"
    )
    parser.add_argument(
        "-crepo",
        "--create_push_gh_repo",
        action="store_true",
        help="Create and push GitHub repository",
    )

    args = parser.parse_args()

    if args.commit_workflow:
        commit_message = input("Enter commit message: ")
        commit_workflow(commit_message)
    elif args.auto_commit:
        auto_commit()
    elif args.clean_up:
        clean_up()
    elif args.init_template:
        init_template()
    elif args.log_graph:
        log_graph()
    elif args.pull_all_dirs:
        pull_all_git_dirs()
    elif args.push_all_dirs:
        push_all_git_dirs()
    elif args.status_all_dirs:
        if status_all_git_dirs():
            sys.exit(0)  # Changes exist
        else:
            sys.exit(1)  # No changes
    elif args.create_push_gh_repo:
        success = create_and_push_gh_repo()
        sys.exit(0 if success else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

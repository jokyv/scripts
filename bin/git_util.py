#!/usr/bin/env python

# -----------------------------------------------
# LIBRARIES
# -----------------------------------------------

import argparse
import os
import subprocess
from datetime import datetime

from rich.console import Console

import python_sops as ps
from messaging import display_message as dm

# -----------------------------------------------
# VARIABLES
# -----------------------------------------------

HOME = os.path.expanduser("~")
PATHS = [f"{HOME}/{ps.get_secret('notes_path')}", f"{HOME}/pics/wallpapers/"]
EXCLUDE_DIRS = [
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
FILE_SIZE_LIMIT = 50  # in MB
# init rich console
console = Console()


# -----------------------------------------------
# FUNCTIONS
# -----------------------------------------------


def auto_commit(paths: list[str]) -> None:
    """
    Function that automatically git commit and push repo list.

    Parameters
    ----------
    paths : list[str]
        list of paths with repos to check, commit and push

    """
    console = Console()

    for path in paths:
        console.print("")
        console.rule("[bold red]Checking repo")
        if not os.path.exists(path):
            dm("FAILURE", f"Path: {path} does not exist.")
            continue

        # dm("INFO", "Pulling all the latest commits")
        # subprocess.run(["git", "pull"], cwd=path)
        dm("CHECKING", f"Any changes for repo: {path}")

        # Run git status to check for changes
        git_status_process = subprocess.run(
            ["git", "status", "--porcelain"], capture_output=True, cwd=path, text=True
        )
        changes_exist = len(git_status_process.stdout.splitlines())

        # if no changes then exit with code 0
        if changes_exist == 0:
            dm("SUCCESS", "Nothing to commit, moving on!")
            console.print("")
        else:
            subprocess.run(["git", "add", "."], cwd=path)
            commit_message = (
                f"auto script backup at: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}"
            )
            subprocess.run(["git", "commit", "-q", "-m", commit_message], cwd=path)
            subprocess.run(["git", "push", "-q"], cwd=path)
            dm("SUCCESS", "Found changes!")
            dm("SUCCESS", "git add, git commit and git push performed")
            console.print("")


def clean_up() -> None:
    # Remove the files from the index (not the actual files in the working copy)
    subprocess.run(["git", "rm", "-r", "--cached", "."])
    # Add these removals to the Staging Area...
    subprocess.run(["git", "add", "."])
    # ...and commit them!
    subprocess.run(["git", "commit", "-m", "Clean up ignored files"])
    # finally do a git push
    subprocess.run(["git", "push"])


def commit_workflow(commit_message):
    # WARNING removing git pull and git stash as i am using git push rebase now
    # Git stash, pull, and apply
    # dm("INFO", "git pull and git stash apply")
    # subprocess.run(["git", "stash", "--include-untracked"])
    # subprocess.run(["git", "pull", "-q"])
    # subprocess.run(["git", "stash", "apply", "-q"])

    dm("CHECKING", f"if any file above {FILE_SIZE_LIMIT} MB exist")
    # Get the path to the git folder
    dir_path = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True
    ).stdout.strip()

    # Check if big files exist before committing
    big_files = subprocess.run(
        ["fd", "-H", ".", dir_path, "--size", f"+{FILE_SIZE_LIMIT}MB", "-gE", ".git"],
        capture_output=True,
        text=True,
    ).stdout.splitlines()
    if big_files:
        dm("WARNING", "file(s) bigger than 50MB exist..")
        dm("WARNING", "delete or ignore the below file(s):")
        for file in big_files:
            print(file)
        return

    dm("SUCCESS", "no big files found!")
    dm("INFO", "proceeding with git add, commit, and push")

    # Git add everything
    subprocess.run(["git", "add", "-A"])
    # Commit change with commit_message but be quiet
    subprocess.run(["git", "commit", "-q", "-m", commit_message])
    # Git push in quiet mode
    subprocess.run(["git", "push", "-q"])

    # Check git status
    dm("INFO", "below is the current git status of the repo")
    subprocess.run(["git", "status", "-sb"])


def init_template() -> None:
    """
    Function that creates a git repo and .gitignore file.

    The script will first check if a .git exist.
    If it does will through an error.
    If it does not then will create a git repo
    Then it will create a .gitignore file with basic exceptions
    Finally will git add and git commit an initial commit

    """
    try:
        # Check if a Git repository already exists
        if os.path.exists(".git"):
            raise FileExistsError("Git repository already exists in this directory.")

        # Initialize Git repository
        os.system("git init")

        # Create .gitignore file
        with open(".gitignore", "w") as f:
            f.write("*.csv\n*.pkl\n*.xlsx\n*.txt\n__pycache__\n")

        # Add .gitignore to staging area
        os.system("git add .gitignore")

        # Commit changes
        os.system('git commit -m "git init and git add - basic git ignore file"')

    except FileExistsError as e:
        print(f"Error: {e}")


def log_graph() -> None:
    git_log_command = [
        "git",
        "log",
        "--graph",
        "--abbrev-commit",
        "--decorate",
        "--format=format:%C(bold green)%h%C(reset) - %C(bold cyan)%aD%C(reset) %C(bold yellow)(%ar)%C(reset)%C(auto)%d%C(reset)%n%C(white)%s%C(reset) %C(dim white)- %an%C(reset)",
        "--all",
    ]
    subprocess.run(git_log_command)


def pull_all_git_dirs() -> None:
    """
    Function git pull all dirs that have git directories.

    The function first will move to HOME dir.
    Using fd will find all folders that have git directory.
    Iterate through git directories executing git pull in async mode.
    """
    # init console
    console = Console()

    # Change to the home directory
    os.chdir(HOME)

    # Use fd to find directories with .git
    # but exclude dirs with names nvim or .local/share
    git_dirs = subprocess.run(
        ["fd", "-td", "-HI", "-g", ".git", *EXCLUDE_DIRS],
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    # Iterate through found git directories
    for git_dir in git_dirs:
        console.print("")
        console.rule("[bold red]Checking repo")

        os.chdir(f"{HOME}/{git_dir}")
        # Move up one directory level
        os.chdir("..")

        dm("CHECKING", f"Anything to pull for repo: {git_dir}")
        subprocess.run(["git", "pull"])


def push_all_git_dirs() -> None:
    """
    Function git push all dirs that have git dir in repos folder.

    The Function first will move to repos dir.
    Using fd will find all git folders in the project dir.
    Then it will iterate through them executing a git push
    with an auto generated message.
    """
    # init rich.console
    console = Console()
    # Change to the project directory
    os.chdir(f"{HOME}/repos")

    # Use fd to find directories with .git
    # but exclude dirs as defined by exclude_dirs variable
    git_dirs = subprocess.run(
        ["fd", "-td", "-HI", "-g", ".git", *EXCLUDE_DIRS],
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    # Iterate through found git directories
    for git_dir in git_dirs:
        os.chdir(f"{HOME}/repos/{git_dir}")

        # Move up one directory level
        os.chdir("..")
        git_status_process = subprocess.run(
            ["git", "status", "-s"], capture_output=True, text=True
        )
        git_status = len(git_status_process.stdout.splitlines())

        if git_status > 0:
            # messaging
            console.print("")
            dm("WARNING", f"{git_dir} repo needs a git commit")

            # Run git add, commit and push
            commit_message = "This is an auto generated git commit!"
            subprocess.run(["git", "add", "."])
            subprocess.run(["git", "commit", "-qm", commit_message])
            subprocess.run(["git", "push", "-q"])
            dm("SUCCESS", "git auto commit was pushed!")


def status_all_git_dirs() -> None:
    # init console
    console = Console()

    # Change to the home directory
    os.chdir(os.path.expanduser("~"))

    # Use fd to find directories with .git
    # but exclude dirs with names .cache, .local/share, or cargo
    git_dirs = subprocess.run(
        ["fd", "-td", "-HI", "-g", ".git", *EXCLUDE_DIRS],
        capture_output=True,
        text=True,
    ).stdout.splitlines()

    # Iterate through found git directories
    for git_dir in git_dirs:
        os.chdir(git_dir)
        # Move up one directory level
        os.chdir("..")
        git_status_process = subprocess.run(
            ["git", "status", "-s"], capture_output=True, text=True
        )
        git_status = len(git_status_process.stdout.splitlines())
        if git_status > 0:
            console.print("")
            dm("WARNING", f"{git_dir} repo needs a git commit")
            subprocess.run(["git", "status", "-sb"])
        # return to HOME
        os.chdir(os.path.expanduser("~"))


# -----------------------------------------------
# MAIN
# -----------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="GIT Utility", description="Utility CLI for GIT custom commands"
    )

    parser.add_argument("-cw", "--commit_workflow", action="store_true")
    parser.add_argument("-ac", "--auto_commit", action="store_true")
    parser.add_argument("-cu", "--clean_up", action="store_true")
    parser.add_argument("-it", "--init_template", action="store_true")
    parser.add_argument("-lg", "--log_graph", action="store_true")
    parser.add_argument("-pld", "--pull_all_dirs", action="store_true")
    parser.add_argument("-pud", "--push_all_dirs", action="store_true")
    parser.add_argument("-std", "--status_all_dirs", action="store_true")

    args = parser.parse_args()
    if args.commit_workflow:
        commit_message = input("Enter commit message: ")
        commit_workflow(commit_message)
    elif args.auto_commit:
        auto_commit(PATHS)
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
        status_all_git_dirs()
    else:
        print("Command was NOT found")

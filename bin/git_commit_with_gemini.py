#!/usr/bin/env python3
"""Generate a git commit message using Gemini AI based on staged changes.

Similar to git_commit_with_gemini.sh but in Python.
"""

import subprocess
import sys
from pathlib import Path

from messaging import display_message


def command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    return subprocess.run(["which", cmd], capture_output=True).returncode == 0


def get_staged_changes() -> str:
    """Get the diff of staged changes."""
    result = subprocess.run(["git", "diff", "--staged"], capture_output=True, text=True)
    return result.stdout


def generate_commit_message(diff: str) -> str:
    """
    Use Gemini CLI to generate a commit message from the diff.

    Returns the commit message or raises an exception if generation fails.
    """
    prompt = (
        "Based on the following git diff, write a concise and descriptive commit message.\n"
        "Reply with ONLY the commit message text, without any extra formatting or explanation.\n\n"
        "--- DIFF ---\n"
        f"{diff}"
    )

    try:
        result = subprocess.run(
            ["gemini", "-p", prompt],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Gemini CLI failed: {e.stderr}") from e
    except FileNotFoundError:
        raise RuntimeError("gemini CLI not found. Please install it.") from None


def main() -> None:
    """Main entry point."""
    # Check for gemini CLI
    if not command_exists("gemini"):
        display_message("error", "gemini CLI not found. Please install it.")
        sys.exit(1)

    # Check if we're in a git repository
    if not Path(".git").exists():
        display_message("error", "Not in a git repository.")
        sys.exit(1)

    # Get staged changes
    display_message("info", "Getting staged changes...")
    changes = get_staged_changes()

    if not changes.strip():
        display_message("info", "No changes to commit.")
        sys.exit(0)

    # Generate commit message
    display_message("info", "Generating commit message with Gemini...")
    try:
        commit_msg = generate_commit_message(changes)
    except RuntimeError as e:
        display_message("error", str(e))
        sys.exit(1)

    if not commit_msg:
        display_message("error", "Failed to generate a commit message.")
        sys.exit(1)

    # Show the commit message and perform commit
    display_message("info", "Committing with the following message:", title="Commit Message")
    display_message("info", commit_msg, panel_style=True)

    try:
        subprocess.run(["git", "commit", "-m", commit_msg], check=True)
        display_message("success", "Commit successful.")
    except subprocess.CalledProcessError as e:
        display_message("error", f"Git commit failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3

import subprocess
import sys
import re
import os
from pathlib import Path


def change_to_repo_root():
    """
    Change the current working directory to the root of the git repository.

    Raises
    ------
    SystemExit
        If not in a git repository or if git command fails
    """
    try:
        repo_root = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            check=True,
            text=True,
            capture_output=True,
        ).stdout.strip()
        os.chdir(repo_root)
    except subprocess.CalledProcessError as e:
        print(f"❌ Not in a git repository or git command failed: {e}")
        sys.exit(1)


def run_cmd(cmd, capture_output=False):
    """
    Run a shell command and optionally capture output.

    Parameters
    ----------
    cmd : str
        The command to execute
    capture_output : bool, optional
        Whether to capture and return the output, by default False

    Returns
    -------
    str or None
        The command output if capture_output is True, otherwise None

    Raises
    ------
    SystemExit
        If the command fails to execute successfully
    """
    try:
        if capture_output:
            result = subprocess.run(cmd, shell=True, check=True, text=True, capture_output=True)
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command '{cmd}' failed with exit code {e.returncode}: {e.stderr}")
        sys.exit(1)


def get_latest_tag():
    """
    Get the latest git tag from the repository.

    Returns
    -------
    str or None
        The latest tag name, or None if no tags exist or an error occurs
    """
    try:
        latest_tag_list = run_cmd("git tag --sort=-v:refname | head -1", capture_output=True)
        return latest_tag_list if latest_tag_list else None
    except SystemExit as e:
        print(f"❌ Failed to get latest tag: {e}")
        return None


def suggest_next_version(release_type, latest_tag):
    """
    Suggest the next semantic version based on the release type and latest tag.

    Parameters
    ----------
    release_type : str
        Type of release: 'major', 'minor', or 'patch'
    latest_tag : str or None
        The latest version tag from the repository

    Returns
    -------
    str
        The suggested next version in 'vX.Y.Z' format

    Notes
    -----
    If no previous tags exist, defaults to v1.0.0 for major, v0.1.0 for minor,
    and v0.0.1 for patch releases
    """
    if latest_tag:
        match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", latest_tag)
        if match:
            major, minor, patch = map(int, match.groups())
            if release_type == "major":
                return f"v{major + 1}.0.0"
            elif release_type == "minor":
                return f"v{major}.{minor + 1}.0"
            elif release_type == "patch":
                return f"v{major}.{minor}.{patch + 1}"
    # Fallback if no tags exist or unexpected format
    if release_type == "major":
        return "v1.0.0"
    elif release_type == "minor":
        return "v0.1.0"
    elif release_type == "patch":
        return "v0.0.1"
    return "v0.1.0"


def deduplicate_changelog():
    """
    Remove duplicate bullet points within the latest release section of CHANGELOG.md .

    git-cliff sometimes emits duplicate entries. This keeps the first occurrence
    of each unique bullet within each subsection of the latest release.
    """
    try:
        text = Path("CHANGELOG.md").read_text()
    except FileNotFoundError:
        print("⚠️  CHANGELOG.md not found, skipping dedup")
        return

    lines = text.splitlines(keepends=True)

    # Find latest release section boundaries
    release_start = None
    release_end = None
    for i, line in enumerate(lines):
        if line.startswith("## [") and release_start is None:
            release_start = i
        elif line.startswith("## [") and release_start is not None:
            release_end = i
            break

    if release_start is None:
        print("⚠️  No release section found, skipping dedup")
        return

    release_end = release_end or len(lines)

    # Deduplicate per subsection within the latest release
    release_lines = lines[release_start:release_end]
    seen_bullets = set()
    out = []
    removed = 0

    for line in release_lines:
        stripped = line.strip()
        if stripped.startswith("### "):
            seen_bullets = set()
            out.append(line)
        elif stripped.startswith("- ") or stripped.startswith("  - "):
            if stripped not in seen_bullets:
                seen_bullets.add(stripped)
                out.append(line)
            else:
                removed += 1
        else:
            out.append(line)

    if removed:
        new_text = "".join(lines[:release_start]) + "".join(out) + "".join(lines[release_end:])
        Path("CHANGELOG.md").write_text(new_text)
        print(f"🧹 Removed {removed} duplicate entries from changelog")
    else:
        print("✓ No duplicates found in changelog")


def main():
    """
    Main function to manage the release process.

    Guides the user through creating a new semantic version release,
    generating a changelog, and pushing the changes to the repository.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Create a new release")
    parser.add_argument(
        "release_type",
        nargs="?",
        choices=["major", "minor", "patch"],
        help="Release type (omit for interactive prompt)",
    )
    parser.add_argument("--yes", "-y", action="store_true", help="Skip confirmation prompt")
    args = parser.parse_args()

    # Ensure we're in the repository root
    change_to_repo_root()

    # 1. Show latest tag
    latest_tag = get_latest_tag()
    if latest_tag:
        print(f"🔎 Latest version: {latest_tag}")
    else:
        print("ℹ️  No existing tags found. Starting from initial version.")

    # 2. Get release type
    release_type = args.release_type
    if not release_type:
        while True:
            release_type = input("Enter release type (major/minor/patch): ").strip().lower()
            if release_type in ["major", "minor", "patch"]:
                break
            print("❌ Please enter 'major', 'minor', or 'patch'")

    # 3. Get the suggested version based on release type
    version = suggest_next_version(release_type, latest_tag)
    print(f"📦 Next version: {version}")

    # 4. Confirm
    if not args.yes:
        confirm = input(f"Proceed with release '{version}'? (yes/no): ").strip().lower()
        if confirm != "yes":
            print("🚫 Release aborted.")
            sys.exit(0)

    # 5. Generate changelog with git-cliff
    print("📝 Generating changelog ...")
    run_cmd(f"git cliff --tag {version} -o CHANGELOG.md")

    # 5b. Deduplicate changelog (inside latest release section)
    deduplicate_changelog()

    # 6. Commit updated changelog
    print("📦 Committing changelog ...")
    run_cmd("git add CHANGELOG.md")
    run_cmd(f"git commit -m 'chore(release): update changelog for {version}'")

    # 7. Create Git tag (AFTER changelog commit)
    print(f"🏷️  Creating tag {version} ...")
    run_cmd(f"git tag {version}")

    # 8. Push tag + changelog
    print("⬆️  Pushing changes ...")
    run_cmd("git push")
    run_cmd("git push --tags")

    print(f"✅ Release {version} created successfully!")


if __name__ == "__main__":
    main()

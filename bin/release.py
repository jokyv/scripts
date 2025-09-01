#!/usr/bin/env python3

import subprocess
import sys
import re
import os

repo_root = subprocess.run(
    ["git", "rev-parse", "--show-toplevel"], check=True, text=True, capture_output=True
).stdout.strip()

os.chdir(repo_root)


def run_cmd(cmd, capture_output=False):
    """Run a shell command and optionally capture output."""
    try:
        if capture_output:
            result = subprocess.run(
                cmd, shell=True, check=True, text=True, capture_output=True
            )
            return result.stdout.strip()
        else:
            subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed: {cmd}\n{e}")
        sys.exit(1)


def get_latest_tag():
    """Get the latest git tag."""
    try:
        latest_tag = run_cmd("git describe --tags --abbrev=0", capture_output=True)
        return latest_tag
    except SystemExit:
        return None


def suggest_next_version(release_type, latest_tag):
    """Suggest the next version based on the latest tag and release type."""
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


def main():
    # 1. Show latest tag
    latest_tag = get_latest_tag()
    if latest_tag:
        print(f"🔎 Latest version: {latest_tag}")
    else:
        print("ℹ️  No existing tags found. Starting from initial version.")

    # 2. Ask for release type
    while True:
        release_type = input("Enter release type (major/minor/patch): ").strip().lower()
        if release_type in ["major", "minor", "patch"]:
            break
        print("❌ Please enter 'major', 'minor', or 'patch'")

    # 3. Suggest next version based on release type
    suggested = suggest_next_version(release_type, latest_tag)
    version = input(f"Enter custom version [current chosen: {suggested}]: ").strip()
    if not version:
        version = suggested

    # 4. Confirm
    confirm = (
        input(f"You are about to tag version '{version}'. Proceed? (yes/no): ")
        .strip()
        .lower()
    )
    if confirm != "yes":
        print("🚫 Aborted.")
        sys.exit(0)

    # 5. Generate changelog with git-cliff
    print("📝 Generating changelog ...")
    run_cmd(f"git cliff --tag {version} -o CHANGELOG.md")

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

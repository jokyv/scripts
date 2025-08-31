#!/usr/bin/env python3

import subprocess
import sys
import re


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


def suggest_next_version():
    """Suggest the next patch version based on the latest tag."""
    try:
        latest_tag = run_cmd("git describe --tags --abbrev=0", capture_output=True)
        print(f"🔎 Latest version found: {latest_tag}")
    except SystemExit:
        return "v0.1.0"  # fallback if no tags exist

    match = re.match(r"v?(\d+)\.(\d+)\.(\d+)", latest_tag)
    if match:
        major, minor, patch = map(int, match.groups())
        return f"v{major}.{minor}.{patch + 1}"
    else:
        # fallback if tag format is unexpected
        return "v0.1.0"


def main():
    # 1. Suggest next version
    suggested = suggest_next_version()
    version = input(f"Enter the new version [default: {suggested}]: ").strip()
    if not version:
        version = suggested

    # 2. Confirm
    confirm = (
        input(f"You are about to tag version '{version}'. Proceed? (yes/no): ")
        .strip()
        .lower()
    )
    if confirm != "yes":
        print("🚫 Aborted.")
        sys.exit(0)

    # 3. Generate changelog with git-cliff
    print("📝 Generating changelog ...")
    run_cmd(f"git cliff --tag {version} -o CHANGELOG.md")

    # 4. Commit updated changelog
    print("📦 Committing changelog ...")
    run_cmd("git add CHANGELOG.md")
    run_cmd(f"git commit -m 'chore(release): update changelog for {version}'")

    # 5. Create Git tag (AFTER changelog commit)
    print(f"🏷️  Creating tag {version} ...")
    run_cmd(f"git tag {version}")

    # 6. Push tag + changelog
    print("⬆️  Pushing changes ...")
    run_cmd("git push")
    run_cmd("git push --tags")

    print(f"✅ Release {version} created successfully!")


if __name__ == "__main__":
    main()

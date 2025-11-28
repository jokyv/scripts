#!/usr/bin/env python3

# -----------------------------------------------
# LIBRARIES
# -----------------------------------------------

import argparse
import os
import subprocess
import sys

from messaging import display_message as dm
from rich.console import Console
from rich.table import Table

# -----------------------------------------------
# VARIABLES
# -----------------------------------------------

console = Console()

LIBRARIES_TO_UPDATE = [
    # visualization
    "altair",
    "hvplot",
    "panel",
    # linting & formating & data hints
    # using ty now
    # "mypy",
    # "pylsp-mypy",  # plugin for mypy
    "python-lsp-server",
    "ruff",
    "ty",
    # scientific computing
    "ipython",
    "numpy",
    "pandas",
    "polars",
    "pyarrow",
    "pydantic",
    # web development
    "fastapi",
    "uvicorn",
    # misc
    "pip",
    "requests",
    "rich",
    "tqdm",
    "uv",
]

# -----------------------------------------------
# FUNCTIONS
# -----------------------------------------------


def get_active_env():
    """Get the current activated venv for python."""
    return os.environ.get("VIRTUAL_ENV")


def is_uv_default_active():
    """Function that checks if 'uv_default' is active."""
    active_env = get_active_env()
    return active_env and "uv_default" in active_env


def get_installed_packages() -> dict[str, str]:
    """
    Get a dictionary of installed packages and their versions using 'uv pip freeze'.
    """
    packages = {}
    try:
        # Use 'uv pip freeze' for a machine-readable output of installed packages
        result = subprocess.run(["uv", "pip", "freeze"], capture_output=True, text=True, check=True)
        for line in result.stdout.strip().split("\n"):
            if "==" in line:
                name, version = line.split("==", 1)
                packages[name.strip()] = version.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        dm("ERROR", "Could not retrieve package list. Is 'uv' installed and in your PATH?")
    return packages


def _display_update_summary(results: dict) -> None:
    """
    Display summary table of pip update results.

    Parameters
    ----------
    results : dict
        Dictionary of result dictionaries with old and new versions.

    """
    if not results:
        dm("SUCCESS", "All libraries are up to date.")
        return

    console.print("\n")
    table = Table(show_header=True, header_style="bold cyan")
    table.add_column("Library", style="dim", width=30)
    table.add_column("Old Version", justify="center")
    table.add_column("New Version", justify="center")
    table.add_column("Status", justify="center")

    sorted_results = sorted(results.items())

    for name, versions in sorted_results:
        old = versions["old"]
        new = versions["new"]

        if old == "not installed":
            status_text = "[green]✓ installed[/green]"
        elif new == "removed":
            status_text = "[yellow]↓ removed[/yellow]"
        else:
            status_text = "[green]↑ upgraded[/green]"

        table.add_row(name, old, new if new != "removed" else "---", status_text)

    console.print(table)


def pip_update_libraries(libraries_to_update: list[str]):
    """
    Update a list of python libraries using uv and summarize changes.

    Parameters
    ----------
    libraries_to_update : list[str]
        List of package names to update
    """
    dm("INFO", "Getting current package versions...")
    before_versions = get_installed_packages()

    dm("CHECKING", f"Checking for updates for {len(libraries_to_update)} libraries...")
    # Let the update process stream its output directly to the user.
    # This provides real-time feedback and shows any errors (like 'not found').
    subprocess.run(["uv", "pip", "install", "-U", *libraries_to_update])

    dm("INFO", "Getting new package versions...")
    after_versions = get_installed_packages()

    results = {}
    # Union of all packages before and after to catch all changes
    all_package_names = sorted(list(set(before_versions.keys()) | set(after_versions.keys())))

    for name in all_package_names:
        old_version = before_versions.get(name)
        new_version = after_versions.get(name)

        # If version is the same, it hasn't changed.
        if old_version == new_version:
            continue

        # A change was detected, record it for the summary table
        if old_version is None:
            results[name] = {"old": "not installed", "new": new_version}
        elif new_version is None:
            results[name] = {"old": old_version, "new": "removed"}
        else:  # Upgraded or Downgraded
            results[name] = {"old": old_version, "new": new_version}

    _display_update_summary(results)


def pip_update_selected_libraries():
    """
    Update a predefined list of libraries.

    Updates all libraries specified in the LIBRARIES_TO_UPDATE constant.
    """
    pip_update_libraries(LIBRARIES_TO_UPDATE)


def pip_update_all_libraries():
    """
    Update all libraries in the current environment.

    Retrieves a list of all installed packages and updates them to their latest versions.
    """
    # Get the list of all libraries
    result = subprocess.run(["uv", "pip", "list"], capture_output=True, text=True)
    lines = result.stdout.strip().split("\n")
    package_names = []

    # Skip the first two lines (headers and separator)
    for line in lines[2:]:
        if " " in line:
            package, _ = line.rsplit(maxsplit=1)
            package_names.append(package.strip())

    if package_names:
        pip_update_libraries(package_names)
    else:
        dm("INFO", "No packages found to update.")


# -----------------------------------------------
# MAIN
# -----------------------------------------------

if __name__ == "__main__":
    active_env = get_active_env()
    if is_uv_default_active():
        print("uv default environment is already active.")
    else:
        print("uv default environment is not active, activate it!!")
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Update Python libraries.")
    parser.add_argument("-A", "--all", action="store_true", help="Update all libraries")
    parser.add_argument("-S", "--selected", action="store_true", help="Update selected libraries")
    args = parser.parse_args()

    if args.all:
        pip_update_all_libraries()
    elif args.selected:
        pip_update_selected_libraries()
    else:
        parser.print_help()

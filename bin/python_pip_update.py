#!/usr/bin/env python3

# -----------------------------------------------
# LIBRARIES
# -----------------------------------------------

import argparse
import os
import subprocess
import sys

from messaging import display_message as dm

# -----------------------------------------------
# VARIABLES
# -----------------------------------------------

LIBRARIES_TO_UPDATE = [
    # visualization 
    "altair",
    "hvplot",
    "panel",

    # linting & formating & data hints
    "mypy",
    "pylsp-mypy",  # plugin for mypy
    "python-lsp-server",
    "ruff",

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


def pip_update_selected_libraries():
    for library in LIBRARIES_TO_UPDATE:
        dm("CHECKING", f"{library}")
        subprocess.run(["uv", "pip", "install", "-U", library], stdout=subprocess.PIPE)


def pip_update_all_libraries():
    # Get the list of all libraries
    all_libraries = subprocess.run(
        ["uv", "pip", "list"], capture_output=True, text=True
    ).stdout

    lines = all_libraries.strip().split("\n")
    package_names = []

    # Skip the first two lines (headers and separator)
    for line in lines[2:]:
        package, _ = line.rsplit(maxsplit=1)
        package_names.append(package.strip())

    for library in package_names:
        dm("CHECKING", f"{library}")
        subprocess.run(["uv", "pip", "install", "-U", library], stdout=subprocess.PIPE)


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
    parser.add_argument(
        "-S", "--selected", action="store_true", help="Update all libraries"
    )
    args = parser.parse_args()

    if args.all:
        pip_update_all_libraries()
    elif args.selected:
        pip_update_selected_libraries()

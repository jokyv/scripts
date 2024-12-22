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
    "altair",
    "fastapi",
    "hvplot",
    "ipython",
    "mypy",
    "numpy",
    "pandas",
    "panel",
    "pip",
    "polars",
    "pyarrow",
    "pydantic",
    "python-lsp-server",
    "pylsp-mypy",  # plugin for mypy
    "requests",
    "rich",
    "ruff",
    "tqdm",
    "uv",
    "uvicorn",
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


# This does NOT work as the de/activation happens on its own process
# the changes does NOT apply to parent shell
# def deactivate_current_env():
#     """Function that deactivates current venv."""
#     if "VIRTUAL_ENV" in os.environ:
#         subprocess.run("deactivate", shell=True, executable="/bin/bash")
#         print("Deactivated current py environment.")


# def activate_uv_default():
#     activate_script = os.path.expanduser("~/uv_default/bin/activate")

#     if not os.path.exists(activate_script):
#         print("UV default activation script not found. Make sure it's created.")
#         sys.exit(1)

#     activate_command = f"source {activate_script}"

#     try:
#         subprocess.run(activate_command, shell=True, check=True, executable="/bin/bash")
#         print("uv default environment activated successfully.")
#     except subprocess.CalledProcessError:
#         print("Failed to activate UV default environment.")
#         sys.exit(1)


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
        # if active_env:
        #     print(f"Another environment is active: {active_env}")
        #     print("Deactivating it...")
        #     deactivate_current_env()

        # print("Activating uv default environment...")
        # activate_uv_default()

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

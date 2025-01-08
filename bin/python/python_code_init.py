#!/usr/bin/env python

"""Script that starts a python project from a template."""

# -----------------------------------------------
# LIBRARIES
# -----------------------------------------------

import os
import subprocess

from messaging import display_message as dm

# -----------------------------------------------
# VARIABLES
# -----------------------------------------------

HOME_DIR = os.path.expanduser("~")
TEMPLATE_PATH = f"{HOME_DIR}/scripts/bin/python/python_project_template.py"

# -----------------------------------------------
# FUNCTIONS
# -----------------------------------------------


def init_code(filename) -> None:
    if not os.path.exists(filename):
        if filename.endswith(".py"):
            dm("INFO", f"created a file with name {filename} from {TEMPLATE_PATH}")
            subprocess.run(["cp", TEMPLATE_PATH, filename])
            subprocess.run(["hx", filename])
        else:
            dm("FAILURE", "The filename does not have `.py` extension.")
    else:
        dm("FAILURE", "Filename already exist, choose another name!!")


# -----------------------------------------------
# MAIN
# -----------------------------------------------

if __name__ == "__main__":
    filename = input("Enter filename of script with `.py` extension: ")
    init_code(filename)

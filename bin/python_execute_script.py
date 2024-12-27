#!/usr/bin/env python

"""Script to check if virtual env is activated."""

# -----------------------------------------------
# LIBRARIES
# -----------------------------------------------

import subprocess
import sys

# -----------------------------------------------
# FUNCTIONS
# -----------------------------------------------


def is_venv_active():
    return hasattr(sys, "real_prefix") or (
        hasattr(sys, "base_prefix") and sys.base_prefix != sys.prefix
    )


def run_script(script_path):
    try:
        subprocess.run([sys.executable, script_path], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error: The script exited with return code {e.returncode}")
    except FileNotFoundError:
        print(f"Error: The script file '{script_path}' was not found.")


# -----------------------------------------------
# MAIN
# -----------------------------------------------


def main():
    if len(sys.argv) < 2:
        print("Press instead: p <path_to_script>")
        sys.exit(1)

    script_path = sys.argv[1]

    if is_venv_active():
        print("Virtual environment is active. Running the specified script...")
        run_script(script_path)
    else:
        print("Error: No virtual environment detected.")
        print("Please activate a virtual environment before running this script.")
        print("You can activate a virtual environment using:")
        print("source /path/to/venv/bin/activate")
        sys.exit(1)


if __name__ == "__main__":
    main()

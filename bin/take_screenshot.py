#!/usr/bin/env python3
"""Take a screenshot with interactive selection using grim and swappy.

Similar to take_screenshot.sh but in Python.
"""

import subprocess
import sys
import time

from messaging import display_message


def command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    return subprocess.run(["which", cmd], capture_output=True).returncode == 0


def main() -> None:
    """Main entry point."""
    # Check dependencies
    for cmd in ["grim", "swappy", "notify-send"]:
        if not command_exists(cmd):
            display_message("error", f"Required command '{cmd}' not found.")
            sys.exit(1)

    display_message("info", "Taking screenshot... Select area with mouse")

    try:
        # Get the selection region from slurp
        slurp_result = subprocess.run(["slurp"], capture_output=True, text=True, check=True)
        selection = slurp_result.stdout.strip()

        # Run grim with the selection and capture output
        grim_process = subprocess.Popen(["grim", "-g", selection, "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # Wait a moment for grim to complete
        stdout, stderr = grim_process.communicate()

        if grim_process.returncode != 0:
            display_message("error", f"Screenshot capture failed: {stderr.decode().strip()}")
            sys.exit(1)

        # Pipe to swappy
        swappy_process = subprocess.run(["swappy", "-f", "-"], input=stdout, capture_output=True)

        if swappy_process.returncode != 0:
            display_message("error", f"Swappy failed: {swappy_process.stderr.decode().strip()}")
            sys.exit(1)

    except Exception as e:
        display_message("error", f"Failed to take screenshot: {e}")
        sys.exit(1)

    # Wait 1 second before notification
    time.sleep(1)

    display_message("success", "Screenshot taken!")
    print("Done.")


if __name__ == "__main__":
    main()

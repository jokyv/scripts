#!/usr/bin/env python3
"""System control script with graphical menu for shutdown, reboot, logout, lock, and sleep.

Similar to my_logout.sh but in Python for better maintainability.
"""

import subprocess
import sys
from pathlib import Path

from messaging import display_message
from rich.console import Console

console = Console()


def command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    return subprocess.run(["which", cmd], capture_output=True).returncode == 0


def format_uptime() -> str:
    """Format uptime string for display."""
    result = subprocess.run(["uptime"], capture_output=True, text=True)
    uptime_line = result.stdout.strip()

    # Parse and format: "up X weeks, Y days, Z hours, W min"
    # Convert to: "Uptime: Xw Yd Zh Wm"
    import re

    match = re.search(r"up\s+(.+?),\s+(\d+)\s+user", uptime_line)
    if match:
        time_str = match.group(1).strip()
        # Replace weeks/days/hours/min with single letters
        time_str = time_str.replace(" weeks", "w").replace(" week", "w")
        time_str = time_str.replace(" days", "d").replace(" day", "d")
        time_str = time_str.replace(" hours", "h").replace(" hour", "h")
        time_str = time_str.replace(" minutes", "m").replace(" minute", "m")
        time_str = time_str.replace(",", "")
        return f"Uptime: {time_str}"

    # Fallback: just use the raw uptime, simplified
    return "Uptime: " + uptime_line.split(",")[0].replace("up ", "").strip()


def confirm_action(action: str) -> bool:
    """
    Show confirmation dialog using fuzzel.

    Returns True if user confirms, False otherwise.
    """
    try:
        result = subprocess.run(
            ["fuzzel", "--prompt", f"Confirm {action}?", "--dmenu"],
            input="Yes\nNo",
            text=True,
            capture_output=True,
        )
        return result.stdout.strip() == "Yes"
    except FileNotFoundError:
        display_message("error", "fuzzel not found, cannot show confirmation dialog")
        return False
    except Exception as e:
        display_message("error", f"Failed to show confirmation: {e}")
        return False


def execute_action(cmd: str) -> bool:
    """Execute a system command with error handling."""
    try:
        subprocess.run(cmd, shell=True, check=True)
        return True
    except subprocess.CalledProcessError:
        display_message("error", f"Failed to execute: {cmd}", title="System Error")
        return False


def check_uncommitted_changes() -> bool:
    """
    Check if there are uncommitted git changes in any tracked repo.

    Uses git_util.py --status_all_dirs which returns 0 if changes exist, 1 if none.
    """
    git_util_path = Path.home() / "scripts" / "bin" / "git_util.py"
    if not git_util_path.exists():
        display_message("warning", "git_util.py not found, skipping git check")
        return False

    try:
        result = subprocess.run(
            [sys.executable, str(git_util_path), "--status_all_dirs"],
            capture_output=True,
        )
        # git_util.py returns 0 when changes exist, 1 when no changes
        return result.returncode == 0
    except Exception as e:
        display_message("error", f"Failed to check git status: {e}")
        return False


def confirm_ignore_changes() -> bool:
    """Ask user if they want to ignore uncommitted changes."""
    try:
        result = subprocess.run(
            ["fuzzel", "--prompt", "Uncommitted changes exist! Shutdown anyway?", "--dmenu"],
            input="Yes\nNo",
            text=True,
            capture_output=True,
        )
        return result.stdout.strip() == "Yes"
    except FileNotFoundError:
        display_message("error", "fuzzel not found")
        return False
    except Exception as e:
        display_message("error", f"Failed to show dialog: {e}")
        return False


def show_menu() -> str:
    """Show the main menu and return the selected option."""
    prompt = format_uptime()
    options = "Shutdown\nReboot\nLogout\nLock\nSleep\nCancel"

    try:
        result = subprocess.run(
            ["fuzzel", "--prompt", f"{prompt} - Please Make a Selection:", "--dmenu"],
            input=options,
            text=True,
            capture_output=True,
        )
        return result.stdout.strip()
    except FileNotFoundError:
        display_message("error", "fuzzel not found. Please install fuzzel.")
        sys.exit(1)
    except Exception as e:
        display_message("error", f"Failed to show menu: {e}")
        sys.exit(1)


def main() -> None:
    """Main entry point."""
    # Check dependencies
    for cmd in ["fuzzel", "swaylock", "notify-send"]:
        if not command_exists(cmd):
            display_message("error", f"Required command '{cmd}' not found.")
            sys.exit(1)

    selection = show_menu()

    match selection:
        case "Shutdown":
            if confirm_action("shutdown"):
                # Check for uncommitted changes
                if check_uncommitted_changes():
                    if confirm_ignore_changes():
                        display_message(
                            "info",
                            "Ignoring uncommitted changes. Performing system shutdown now",
                            title="Shutting down",
                        )
                        if execute_action("systemctl poweroff"):
                            sys.exit(0)
                        else:
                            sys.exit(1)
                    else:
                        msg = "Shutdown was canceled due to uncommitted changes"
                        display_message("info", msg, title="Shutdown canceled")
                        sys.exit(0)
                else:
                    display_message("info", "Performing system shutdown now", title="Shutting down")
                    if execute_action("systemctl poweroff"):
                        sys.exit(0)
                    else:
                        sys.exit(1)
            else:
                display_message("info", "Shutdown was canceled", title="Shutdown canceled")
                sys.exit(0)

        case "Reboot":
            if confirm_action("reboot"):
                if execute_action("systemctl reboot"):
                    sys.exit(0)
                else:
                    sys.exit(1)
            else:
                display_message("info", "Reboot was canceled", title="Reboot canceled")
                sys.exit(0)

        case "Logout":
            if confirm_action("logout"):
                if execute_action("pkill niri"):
                    sys.exit(0)
                else:
                    sys.exit(1)
            else:
                display_message("info", "Logout was canceled", title="Logout canceled")
                sys.exit(0)

        case "Lock":
            execute_action("swaylock -f")
            sys.exit(0)

        case "Sleep":
            if confirm_action("sleep"):
                if execute_action("systemctl suspend"):
                    sys.exit(0)
                else:
                    sys.exit(1)
            else:
                display_message("info", "Sleep was canceled", title="Sleep canceled")
                sys.exit(0)

        case "Cancel" | "":
            sys.exit(0)

        case _:
            display_message("warning", f"Unknown selection: {selection}")
            sys.exit(1)


if __name__ == "__main__":
    main()

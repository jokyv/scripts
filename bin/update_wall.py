#!/usr/bin/env python3
"""Wallpaper management utility with auto-rotation daemon.

Similar to update_wall.sh but in Python.
"""

import argparse
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

from messaging import display_message
from rich.console import Console

console = Console()

# Configuration
WALLPAPERS_DIR = Path.home() / "pics" / "wallpapers"
DEFAULT_LOOP_INTERVAL = 15 * 60  # 15 minutes in seconds


def command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    return subprocess.run(["which", cmd], capture_output=True).returncode == 0


def check_dependencies() -> None:
    """Check for required commands."""
    for cmd in ["swww", "notify-send", "pgrep"]:
        if not command_exists(cmd):
            display_message("error", f"Required command '{cmd}' not found.")
            sys.exit(1)


def ensure_swww_daemon() -> None:
    """Ensure swww-daemon is running."""
    try:
        # Check if swww-daemon is already running
        result = subprocess.run(["pgrep", "-f", "swww-daemon"], capture_output=True)
        if result.returncode == 0:
            return  # Already running

        # Start it in background
        subprocess.Popen(
            ["swww-daemon"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        time.sleep(1)  # Give it a moment to start
    except Exception as e:
        display_message("error", f"Failed to start swww-daemon: {e}")
        sys.exit(1)


def format_uptime() -> str:
    """Format uptime string for menu display."""
    try:
        result = subprocess.run(["uptime"], capture_output=True, text=True, check=True)
        uptime_line = result.stdout.strip()

        # Parse: "up X weeks, Y days, Z hours, W min"
        import re

        match = re.search(r"up\s+(.+?),\s+(\d+)\s+user", uptime_line)
        if match:
            time_str = match.group(1).strip()
            time_str = time_str.replace(" weeks", "w").replace(" week", "w")
            time_str = time_str.replace(" days", "d").replace(" day", "d")
            time_str = time_str.replace(" hours", "h").replace(" hour", "h")
            time_str = time_str.replace(" minutes", "m").replace(" minute", "m")
            time_str = time_str.replace(",", "")
            return f"Uptime: {time_str}"

        # Fallback
        return "Uptime: " + uptime_line.split(",")[0].replace("up ", "").strip()
    except Exception:
        return "Uptime: N/A"


def find_wallpaper(wallpapers_dir: Path) -> Path | None:
    """Find a random wallpaper from the directory."""
    if not wallpapers_dir.exists():
        display_message("error", f"Wallpaper directory not found: {wallpapers_dir}")
        return None

    try:
        # Find files, excluding .git and .gitignore
        result = subprocess.run(
            [
                "find",
                str(wallpapers_dir),
                "-type",
                "f",
                "-not",
                "-path",
                "*/\\.git/*",
                "-not",
                "-name",
                ".gitignore",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
        files = [f.strip() for f in result.stdout.splitlines() if f.strip()]

        if not files:
            display_message("error", f"No wallpapers found in {wallpapers_dir}")
            return None

        import random

        return Path(random.choice(files))
    except subprocess.CalledProcessError as e:
        display_message("error", f"Failed to list wallpapers: {e}")
        return None
    except Exception as e:
        display_message("error", f"Unexpected error: {e}")
        return None


def apply_wallpaper(wallpaper_path: Path) -> bool:
    """Apply the wallpaper using swww."""
    try:
        subprocess.run(
            [
                "swww",
                "img",
                str(wallpaper_path),
                "--transition-fps",
                "60",
                "--transition-type",
                "any",
                "--transition-duration",
                "3",
            ],
            check=True,
        )
        return True
    except subprocess.CalledProcessError as e:
        display_message("error", f"Failed to set wallpaper: {e}")
        return False


def change_wallpaper(wallpapers_dir: Path | None = None, notification_type: str = "manual") -> bool:
    """Change to a random wallpaper."""
    if wallpapers_dir is None:
        wallpapers_dir = WALLPAPERS_DIR

    wallpaper = find_wallpaper(wallpapers_dir)
    if wallpaper is None:
        return False

    if apply_wallpaper(wallpaper):
        filename = wallpaper.name
        title = "Wallpaper Auto-Rotated" if notification_type == "auto" else "Wallpaper Updated"
        display_message("success", f"Now displaying: {filename}", title=title)
        return True
    return False


def run_loop(interval: int = DEFAULT_LOOP_INTERVAL) -> None:
    """Daemon loop: change wallpaper every interval seconds."""
    display_message("info", f"Wallpaper daemon started, rotating every {interval} seconds", title="Wallpaper Loop")
    while True:
        time.sleep(interval)
        change_wallpaper(notification_type="auto")


def get_daemon_pid() -> int | None:
    """Find the PID of the wallpaper daemon if running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", f"{sys.argv[0]} --loop-daemon"],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split()
            if pids:
                return int(pids[0])
    except Exception:
        pass
    return None


def toggle_loop(interval: int | None = None) -> None:
    """Toggle the auto-rotation daemon on or off."""
    if interval is None:
        interval = DEFAULT_LOOP_INTERVAL

    pid = get_daemon_pid()

    if pid is not None:
        # Daemon is running - kill it
        try:
            os.kill(pid, signal.SIGTERM)
            time.sleep(0.5)  # Give it time to terminate
            # Double-check
            if get_daemon_pid() is not None:
                os.kill(pid, signal.SIGKILL)
            display_message("info", "Stopped automatic wallpaper changing.", title="Wallpaper Loop")
        except ProcessLookupError:
            display_message("warning", "Daemon was not running when trying to stop.")
        except Exception as e:
            display_message("error", f"Failed to stop daemon: {e}")
        return

    # Start the daemon
    script_path = Path(sys.argv[0]).resolve()
    try:
        # Use nohup to detach, redirect output to /dev/null
        subprocess.Popen(
            [sys.executable, str(script_path), "--loop-daemon", str(interval)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,  # Detach from parent
        )
        # Short delay to ensure it started
        time.sleep(0.5)
        if get_daemon_pid() is not None:
            minutes = interval // 60
            msg = f"Started automatic wallpaper changing every {minutes} minutes."
            display_message("success", msg, title="Wallpaper Loop")
        else:
            display_message("warning", "Daemon may have failed to start.")
    except Exception as e:
        display_message("error", f"Failed to start daemon: {e}")


def main() -> None:
    """Main entry point."""
    check_dependencies()
    ensure_swww_daemon()

    parser = argparse.ArgumentParser(description="Wallpaper management with auto-rotation")
    parser.add_argument(
        "--auto-rotate",
        action="store_true",
        help="Toggle automatic wallpaper rotation on/off",
    )
    parser.add_argument(
        "--loop-daemon",
        action="store_true",
        help=argparse.SUPPRESS,  # Internal use only
    )
    parser.add_argument(
        "wallpapers_dir", nargs="?", default=None, help=f"Directory containing wallpapers (default: {WALLPAPERS_DIR})"
    )

    args = parser.parse_args()

    if args.loop_daemon:
        # Internal daemon mode - run the rotation loop
        run_loop()
        return

    if args.auto_rotate:
        # Toggle the daemon on/off
        toggle_loop()
        return

    # Default: change wallpaper once, optionally with custom dir
    wallpapers_dir_path = Path(args.wallpapers_dir) if args.wallpapers_dir else None
    change_wallpaper(wallpapers_dir_path)


if __name__ == "__main__":
    main()

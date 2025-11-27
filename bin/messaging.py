#!/usr/bin/env python

# -----------------------------------------------
# LIBRARIES
# -----------------------------------------------

import argparse
import logging
import os
import re
import time
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.logging import RichHandler
from rich.panel import Panel
from rich.spinner import Spinner
from rich.table import Table
from rich.text import Text

# -----------------------------------------------
# LOGGING CONFIGURATION
# -----------------------------------------------


class MarkupStrippingFormatter(logging.Formatter):
    """Custom formatter to strip rich markup for plain text logging."""

    def format(self, record):
        formatted_message = super().format(record)
        # Strip rich markup like [bold blue]...[/]
        return re.sub(r"\[[^\]]*\]", "", formatted_message)


# Decide log file path: persistent under /var/log, else /tmp fallback
LOG_FILE = "/var/log/my-app/app.log"
try:
    Path("/var/log/my-app").mkdir(parents=True, exist_ok=True)
    Path(LOG_FILE).touch(exist_ok=True)
except PermissionError:
    LOG_FILE = "/tmp/app.log"
    Path(LOG_FILE).touch(exist_ok=True)

# Handlers: Rich console + rotating file
console_handler = RichHandler(
    rich_tracebacks=True,
    markup=True,
    show_time=True,
    show_level=True,
    show_path=False,
)

file_handler = RotatingFileHandler(
    LOG_FILE,
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3,
    encoding="utf-8",
)
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(MarkupStrippingFormatter("%(asctime)s - %(levelname)s - %(message)s"))

# Configure both handlers (force replaces any old config)
logging.basicConfig(level=logging.INFO, format="%(message)s", handlers=[console_handler, file_handler], force=True)
# Create logger instance
logger = logging.getLogger("rich")
# Add console instance
console = Console()

# Enhanced message categories with icons and colors
MESSAGE_THEMES = {
    "warning": {"icon": "⚠", "color": "red", "style": "bold red"},
    "info": {"icon": "ℹ", "color": "blue", "style": "bold blue"},
    "success": {"icon": "✓", "color": "green", "style": "bold green"},
    "failure": {"icon": "✗", "color": "red", "style": "bold red"},
    "error": {"icon": "✗", "color": "red", "style": "bold red"},  # Alias for failure
    "checking": {"icon": "⟳", "color": "yellow", "style": "bold yellow"},
    "debug": {"icon": "🐛", "color": "magenta", "style": "bold magenta"},
    "question": {"icon": "?", "color": "cyan", "style": "bold cyan"},
    "star": {"icon": "⭐", "color": "yellow", "style": "bold yellow"},
}


# -----------------------------------------------
# FUNCTIONS
# -----------------------------------------------


def display_message(level: str, message: str, title: str = None, panel_style: bool = False) -> None:
    """
    Display a message with rich formatting, icons, and optional panels.

    Parameters
    ----------
    level : str
        Message level (warning, info, success, failure, checking, debug, question, star)
    message : str
        The message content
    title : str, optional
        Optional title for panel display
    panel_style : bool, default=False
        Whether to display in a rich panel
    """
    level_lower = level.lower()

    if level_lower not in MESSAGE_THEMES:
        valid_levels = list(MESSAGE_THEMES.keys())
        raise ValueError(f"Invalid level: {level_lower}. Valid options: {valid_levels}")

    theme = MESSAGE_THEMES[level_lower]
    icon_text = f"{theme['icon']} "

    if panel_style:
        # Create a beautiful panel
        panel_title = title or level_lower.upper()
        styled_message = Text.from_markup(f"[{theme['color']}]{icon_text}{message}[/]")

        console.print(
            Panel(
                styled_message,
                title=f"[bold {theme['color']}]{panel_title}[/]",
                border_style=theme["color"],
                padding=(1, 2),
            )
        )
    else:
        # Standard rich logging
        logger.info(f"[{theme['style']}]{icon_text}{message}[/]")


def display_progress(message: str, duration: float = 2.0) -> None:
    """
    Show an animated progress spinner.

    Parameters
    ----------
    message : str
        Message to display during progress
    duration : float
        How long to show the spinner (seconds)
    """
    with Live(Spinner("dots", text=message), refresh_per_second=20) as live:
        time.sleep(duration)
        live.update(Spinner("dots", text=f"[green]✓ {message} - Completed![/green]"))
        time.sleep(0.5)


def confirm_action(message: str, default: bool = True) -> bool:
    """
    Display a confirmation dialog.

    Parameters
    ----------
    message : str
        Question to ask user
    default : bool, default=True
        Default response if user presses Enter

    Returns
    -------
    bool
        User's confirmation
    """
    suffix = "[Y/n]" if default else "[y/N]"
    response = input(f"{message} {suffix} ").strip().lower()

    if response == "":
        return default
    return response in ["y", "yes"]


def display_messages_table(messages: list, title: str = "Messages Summary") -> None:
    """
    Display multiple messages in a beautiful table.

    Parameters
    ----------
    messages : list
        List of (level, message) tuples
    title : str
        Table title
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Status", width=12)
    table.add_column("Message", style="white")

    for level, message in messages:
        theme = MESSAGE_THEMES.get(level, MESSAGE_THEMES["info"])
        table.add_row(f"[{theme['style']}]{theme['icon']} {level.upper()}[/]", message)

    console.print(table)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Rich messaging utility")
    parser.add_argument("level", help="Message level", choices=list(MESSAGE_THEMES.keys()))
    parser.add_argument("message", help="Message content")
    parser.add_argument("--title", help="Panel title")
    parser.add_argument("--panel", action="store_true", help="Display in panel")

    return parser.parse_args()


# -----------------------------------------------
# MAIN
# -----------------------------------------------


def main() -> None:
    """Demo all the wow features."""

    # If command line arguments provided, use CLI mode
    try:
        args = parse_args()
        display_message(args.level, args.message, args.title, args.panel)
        return
    except SystemExit:
        # No CLI args, run demo mode
        pass

    # Demo mode - show all features
    display_message("info", "System initialized successfully")
    display_message("success", "All checks passed!")

    # Panel messages
    display_message("warning", "Backup scheduled for 2:00 AM", "System Alert", panel_style=True)
    display_message("star", "You've reached a milestone!", "Achievement", panel_style=True)

    # Progress demo
    display_progress("Processing data...", 3.0)

    # Table demo
    messages = [
        ("success", "Database connection established"),
        ("warning", "Cache needs cleanup"),
        ("info", "User session active"),
        ("failure", "Email service unavailable"),
    ]
    display_messages_table(messages)

    # Confirmation demo
    if confirm_action("Do you want to continue?"):
        display_message("success", "Action confirmed!")
    else:
        display_message("info", "Action cancelled")


if __name__ == "__main__":
    main()

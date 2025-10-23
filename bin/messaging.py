#!/usr/bin/env python

# -----------------------------------------------
# LIBRARIES
# -----------------------------------------------

import logging

from rich.logging import RichHandler
from rich.theme import Theme

# -----------------------------------------------
# LOGGING CONFIGURATION
# -----------------------------------------------

# Configure logging with Rich handler
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[
        RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=True,  # Keep timestamp
            show_level=True,  # Keep level display
            show_path=False,  # Disable only file path
        )
    ],
)

# Create logger instance
logger = logging.getLogger("rich")

# Keep these for backward compatibility
LEVEL: str = "info"
MESSAGE: str = "you did it!"
CUSTOM_THEME = Theme({"warning": "red", "info": "magenta", "success": "green", "failure": "red", "checking": "yellow"})

# -----------------------------------------------
# FUNCTIONS
# -----------------------------------------------


def display_message(level: str, message: str) -> None:
    """
    Display a message with specified level using rich.Console.

    Parameters
    ----------
    level : str
        The level of the message (warning, info, success, failure, check).
    message : str
        The message to display.

    Raises
    ------
    ValueError
        If invalid level is provided

    Examples
    --------
    display_message("warning", "This is a warning message.")
    display_message("info", "Checking something...")
    display_message("success", "Task completed successfully!")
    display_message("failure", "Task failed!")
    display_message("checking", "Checking for updates")

    """
    level_lower = level.lower()

    # Map custom levels to logging levels
    level_mapping = {
        "warning": logging.WARNING,
        "info": logging.INFO,
        "success": logging.INFO,  # Use INFO for success with custom styling
        "failure": logging.ERROR,
        "checking": logging.INFO,  # Use INFO for checking with custom styling
    }

    if level_lower not in level_mapping:
        valid_levels = ["warning", "info", "success", "failure", "checking"]
        raise ValueError(f"Invalid level: {level}. Valid options: {valid_levels}")

    # Log with appropriate level
    if level_lower == "success":
        logger.info(f"[green]✓ {message}[/green]")
    elif level_lower == "checking":
        logger.info(f"[yellow]⟳ {message}[/yellow]")
    else:
        logger.log(level_mapping[level_lower], message)


# -----------------------------------------------
# MAIN
# -----------------------------------------------


def main() -> None:
    # Test all message levels
    display_message("info", "This is an info message")
    display_message("warning", "This is a warning message")
    display_message("success", "Task completed successfully!")
    display_message("failure", "Task failed!")
    display_message("checking", "Checking for updates")


if __name__ == "__main__":
    main()

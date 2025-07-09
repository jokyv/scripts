#!/usr/bin/env python

# -----------------------------------------------
# LIBRARIES
# -----------------------------------------------

from rich.console import Console
from rich.errors import MissingStyle
from rich.theme import Theme

# -----------------------------------------------
# VARIABLES
# -----------------------------------------------

LEVEL: str = "info"
MESSAGE: str = "you did it!"
CUSTOM_THEME = Theme({
    "warning": "red",
    "info": "magenta",
    "success": "green",
    "failure": "red",
    "checking": "yellow",
})

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
    display_message("checking", "for updates")

    """
    level_lower = level.lower()
    match level_lower:
        case "warning" | "info" | "success" | "failure" | "checking":
            pass
        case _:
            valid_levels = ["warning", "info", "success", "failure", "checking"]
            raise ValueError(f"Invalid level: {level}. Valid options: {valid_levels}")

    console = Console(theme=CUSTOM_THEME)
    try:
        console.print(f"[bold]:: {level}[/bold] -", message, style=level_lower)
    except MissingStyle:
        console.print("[bold red]:: Error! - wrong color for rich library[/bold red]")


# -----------------------------------------------
# MAIN
# -----------------------------------------------


def main() -> None:
    display_message(LEVEL, MESSAGE)


if __name__ == "__main__":
    main()

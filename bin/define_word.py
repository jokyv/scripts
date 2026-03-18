#!/usr/bin/env python3
"""Look up a word definition using dictionaryapi.dev and show in notification.

Similar to define_word.sh but in Python.
"""

import json
import subprocess
import sys

import requests
from messaging import display_message


def command_exists(cmd: str) -> bool:
    """Check if a command exists in PATH."""
    return subprocess.run(["which", cmd], capture_output=True).returncode == 0


def get_word_from_clipboard() -> str:
    """Get the word from the primary clipboard (Wayland)."""
    try:
        result = subprocess.run(["wl-paste", "--primary"], capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        display_message("error", "Failed to get word from clipboard.")
        return ""


def lookup_word(word: str) -> dict | None:
    """Look up a word using the dictionary API."""
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en_US/{word}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        display_message("error", f"Failed to lookup word: {e}")
        return None
    except json.JSONDecodeError as e:
        display_message("error", f"Invalid response from API: {e}")
        return None


def format_definitions(data: dict, max_definitions: int = 3) -> str:
    """
    Format definitions from API response.

    Returns a string with part of speech and definition.
    """
    definitions = []

    for entry in data:
        for meaning in entry.get("meanings", []):
            pos = meaning.get("partOfSpeech", "")
            for definition_obj in meaning.get("definitions", []):
                definition = definition_obj.get("definition", "")
                if definition:
                    definitions.append(f"{pos}. {definition}")
                if len(definitions) >= max_definitions:
                    break
            if len(definitions) >= max_definitions:
                break
        if len(definitions) >= max_definitions:
            break

    return "\n".join(definitions) if definitions else "No definitions found."


def show_notification(title: str, message: str) -> None:
    """Show a desktop notification."""
    try:
        subprocess.run(
            ["notify-send", title, message],
            check=True,
        )
    except subprocess.CalledProcessError as e:
        display_message("warning", f"Failed to show notification: {e}")
    except FileNotFoundError:
        display_message("warning", "notify-send not found, cannot show notification")


def main() -> None:
    """Main entry point."""
    # Check for notify-send
    if not command_exists("notify-send"):
        display_message("error", "Required command 'notify-send' not found.")
        sys.exit(1)

    # Get word from argument or clipboard
    if len(sys.argv) > 1:
        word = sys.argv[1]
    else:
        display_message("info", "No word provided, getting from clipboard...")
        word = get_word_from_clipboard()

    if not word:
        display_message("error", "No word provided and clipboard empty.")
        sys.exit(1)

    display_message("info", f"Looking up: {word}")

    # Look up the word
    data = lookup_word(word)
    if not data:
        show_notification("Invalid word.", "")
        sys.exit(0)

    # Format definitions (first 3)
    def_text = format_definitions(data, max_definitions=3)

    if not def_text:
        show_notification(f"{word} -", "No definitions found.")
        sys.exit(0)

    # Show notification
    show_notification(f"{word} -", def_text)

    # Also print to stdout for terminal use
    print(f"\n{def_text}")


if __name__ == "__main__":
    main()

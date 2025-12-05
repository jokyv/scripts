#!/usr/bin/env python3

import sys
import subprocess
import argparse


def send_notification(title, message, criticality):
    """Send desktop notification"""
    try:
        subprocess.run(["notify-send", "-u", criticality, title, message], check=True)
    except subprocess.CalledProcessError:
        pass


def paste_clipboard():
    """Paste the current clipboard content"""
    try:
        wl_paste = subprocess.Popen(["wl-paste"], stdout=subprocess.PIPE)
        content = wl_paste.communicate()[0].decode().strip()

        if not content:
            send_notification("Clipboard Paste", "Nothing to paste - clipboard is empty", "critical")
            return

        subprocess.run(["wtype", content])
        send_notification(
            "Clipboard Paste",
            f"Pasted: {content[:50]}{'...' if len(content) > 50 else ''}",
            "normal",
        )
    except FileNotFoundError:
        send_notification("Error", "wtype is not installed", "critical")
        sys.exit(1)
    except subprocess.CalledProcessError:
        send_notification("Error", "Failed to paste content", "critical")
        sys.exit(1)


def add_to_history():
    """Add highlighted text to both cliphist and regular clipboard"""
    try:
        highlighted = subprocess.check_output(["wl-paste", "-p"]).decode().strip()

        if not highlighted:
            send_notification("Clipboard History", "No text is currently highlighted", "critical")
            return

        subprocess.run(["cliphist", "store"], input=highlighted.encode())
        subprocess.run(["wl-copy"], input=highlighted.encode())

        send_notification(
            "Clipboard History",
            f"Added to history: {highlighted[:50]}{'...' if len(highlighted) > 50 else ''}",
            "normal",
        )
    except subprocess.CalledProcessError:
        send_notification("Error", "Failed to add text to history", "critical")
        sys.exit(1)


def select_from_history():
    """Run fuzzel selection interface for cliphist"""
    try:
        list_process = subprocess.Popen(["cliphist", "list"], stdout=subprocess.PIPE)

        fuzzel_process = subprocess.Popen(["fuzzel", "--dmenu"], stdin=list_process.stdout, stdout=subprocess.PIPE)
        list_process.stdout.close()

        selected = fuzzel_process.communicate()[0].decode().strip()
        if not selected:
            send_notification("Clipboard History", "No selection made", "critical")
            return

        decode_process = subprocess.Popen(["cliphist", "decode"], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        decoded = decode_process.communicate(input=selected.encode())[0]

        subprocess.run(["wl-copy"], input=decoded)

        notification_text = decoded.decode().strip()
        send_notification(
            "Clipboard Selection",
            f"Copied: {notification_text[:50]}{'...' if len(notification_text) > 50 else ''}",
            "normal",
        )

    except subprocess.CalledProcessError:
        send_notification("Error", "Failed to select from history", "critical")
        sys.exit(1)


def delete_from_history():
    """Delete selected entry from cliphist history"""
    try:
        # Get list of entries
        list_process = subprocess.Popen(["cliphist", "list"], stdout=subprocess.PIPE)

        # Select entry to delete using fuzzel
        fuzzel_process = subprocess.Popen(["fuzzel", "--dmenu"], stdin=list_process.stdout, stdout=subprocess.PIPE)
        list_process.stdout.close()

        selected = fuzzel_process.communicate()[0].decode().strip()
        if not selected:
            send_notification("Clipboard History", "No selection made", "critical")
            return

        # Extract entry ID (cliphist entries are in format "ID\tCONTENT")
        entry_id = selected.split("\t")[0]
        entry = selected.split("\t")[1]

        # Delete the selected entry
        subprocess.run(["cliphist", "delete-query", entry], check=True)

        send_notification(
            "Clipboard History",
            f"Deleted id: {entry_id} with entry: {entry[:50]}{'...' if len(entry) > 50 else ''}",
            "critical",
        )

    except subprocess.CalledProcessError as e:
        send_notification("Error", f"Failed to delete entry: {str(e)}", "critical")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Clipboard history management tool")
    parser.add_argument(
        "command",
        choices=["add", "sel", "paste", "del"],
        help="Command to execute (add: add highlighted text, sel: select from history, paste: paste current clipboard, del: delete entry)",
    )

    args = parser.parse_args()

    if args.command == "add":
        add_to_history()
    elif args.command == "sel":
        select_from_history()
    elif args.command == "paste":
        paste_clipboard()
    elif args.command == "del":
        delete_from_history()


if __name__ == "__main__":
    main()

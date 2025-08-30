#!/usr/bin/env python3
"""Script to manage and open browser bookmarks with fuzzel selection."""

import argparse
import json
import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple, Union


def get_browser_bookmarks(browser: str) -> Union[List[Tuple[str, str]], List[str]]:
    """
    Extract bookmarks from the specified browser.
    
    Args:
        browser: Either 'firefox' or 'brave'
    
    Returns:
        For Firefox: List of (title, url) tuples
        For Brave: List of URL strings
    """
    if browser == "firefox":
        # Find Firefox profile
        profile_path = next(Path("~/.mozilla/firefox").expanduser().glob("*.default-release"), None)
        if not profile_path:
            raise FileNotFoundError("Firefox profile not found")
        
        # Access SQLite database
        db_path = profile_path / "places.sqlite"
        if not db_path.exists():
            raise FileNotFoundError("Firefox bookmarks database not found")
        
        # Query bookmarks
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT b.title, p.url FROM moz_bookmarks b "
            "JOIN moz_places p ON b.fk = p.id "
            "WHERE b.type = 1 AND b.title != '' "
            "ORDER BY b.dateAdded DESC"
        )
        return cursor.fetchall()
    
    elif browser == "brave":
        # Access Brave bookmarks file
        bookmarks_path = Path("~/.config/BraveSoftware/Brave-Browser/Default/Bookmarks").expanduser()
        if not bookmarks_path.exists():
            raise FileNotFoundError("Brave bookmarks file not found")
        
        # Parse JSON and extract URLs
        with open(bookmarks_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        urls = []
        # Recursively extract URLs from bookmarks JSON structure
        def extract_urls(node):
            if isinstance(node, dict):
                if "url" in node:
                    urls.append(node["url"])
                for value in node.values():
                    extract_urls(value)
            elif isinstance(node, list):
                for item in node:
                    extract_urls(item)
        
        extract_urls(data)
        return urls
    
    else:
        raise ValueError(f"Unsupported browser: {browser}")


def show_bookmarks_with_fuzzel(bookmarks: Union[List[Tuple[str, str]], List[str]], browser: str) -> str:
    """
    Display bookmarks using fuzzel and return selected URL.
    
    Args:
        bookmarks: Bookmarks data structure specific to the browser
        browser: Browser type to format output appropriately
    """
    if browser == "firefox":
        # Format as "title\turl" for Firefox
        input_text = "\n".join(f"{title}\t{url}" for title, url in bookmarks)
    else:
        # Just URLs for Brave
        input_text = "\n".join(bookmarks)
    
    try:
        result = subprocess.run(
            ["fuzzel", "-d", "-p", f"Select a {browser.capitalize()} bookmark: "],
            input=input_text,
            text=True,
            capture_output=True,
            check=True
        )
        selected = result.stdout.strip()
        if browser == "firefox" and selected:
            # Extract URL from "title\turl" format
            selected = selected.split('\t')[1] if '\t' in selected else selected
        return selected
    except subprocess.CalledProcessError:
        return ""


def open_url_in_browser(url: str, browser: str) -> None:
    """Open the selected URL in the specified browser."""
    browser_cmd = "firefox" if browser == "firefox" else "brave"
    subprocess.run([browser_cmd, url], check=False)


def main() -> None:
    """Main function to handle browser bookmark selection."""
    parser = argparse.ArgumentParser(description="Open browser bookmarks with fuzzel")
    parser.add_argument(
        "-b", "--browser",
        default="firefox",
        choices=["firefox", "brave"],
        help="Browser to get bookmarks from (default: firefox)"
    )
    parser.add_argument(
        "-f", "--firefox",
        action="store_const",
        const="firefox",
        dest="browser",
        help="Use Firefox bookmarks (default)"
    )
    parser.add_argument(
        "-r", "--brave",
        action="store_const",
        const="brave",
        dest="browser",
        help="Use Brave bookmarks"
    )
    
    args = parser.parse_args()
    
    try:
        bookmarks = get_browser_bookmarks(args.browser)
        selected_url = show_bookmarks_with_fuzzel(bookmarks, args.browser)
        
        if selected_url:
            open_url_in_browser(selected_url, args.browser)
            
    except (FileNotFoundError, sqlite3.Error, json.JSONDecodeError, ValueError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nOperation cancelled", file=sys.stderr)
        sys.exit(0)


if __name__ == "__main__":
    main()

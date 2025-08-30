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
        For Brave: List of (title, url) tuples
    """
    if browser == "firefox":
        # Find Firefox profile directory
        firefox_dir = Path("~/.mozilla/firefox").expanduser()
        if not firefox_dir.exists():
            raise FileNotFoundError("Firefox directory not found")
        
        # Look for profiles.ini to find the default profile
        profiles_ini = firefox_dir / "profiles.ini"
        profile_path = None
        
        if profiles_ini.exists():
            # Parse profiles.ini to find the default profile
            import configparser
            config = configparser.ConfigParser()
            config.read(profiles_ini)
            
            for section in config.sections():
                if section.startswith('Profile') and config.get(section, 'Default', fallback='0') == '1':
                    path = config.get(section, 'Path', fallback='')
                    if path:
                        profile_path = firefox_dir / path
                        break
                # If no default found, try to find any profile with IsRelative=1
                if profile_path is None and section.startswith('Profile'):
                    if config.get(section, 'IsRelative', fallback='0') == '1':
                        path = config.get(section, 'Path', fallback='')
                        if path:
                            profile_path = firefox_dir / path
        else:
            # Fallback: try to find any directory ending with .default or .default-release
            for pattern in ["*.default", "*.default-release"]:
                profile_path = next(firefox_dir.glob(pattern), None)
                if profile_path:
                    break
        
        if not profile_path or not profile_path.exists():
            raise FileNotFoundError("Firefox profile not found")
        
        # Access SQLite database
        db_path = profile_path / "places.sqlite"
        if not db_path.exists():
            raise FileNotFoundError("Firefox bookmarks database not found")
        
        # Query bookmarks
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT b.title, p.url FROM moz_bookmarks b "
            "JOIN moz_places p ON b.fk = p.id "
            "WHERE b.type = 1 AND b.title IS NOT NULL AND b.title != '' "
            "ORDER BY b.dateAdded DESC"
        )
        results = cursor.fetchall()
        conn.close()
        return results
    
    elif browser == "brave":
        # Try multiple possible paths for Brave bookmarks
        possible_paths = [
            Path("~/.config/BraveSoftware/Brave-Browser/Default/Bookmarks").expanduser(),
            Path("~/.config/BraveSoftware/Brave-Browser/Profile 1/Bookmarks").expanduser(),
            Path("~/.config/brave/Default/Bookmarks").expanduser(),
        ]
        
        bookmarks_path = None
        for path in possible_paths:
            if path.exists():
                bookmarks_path = path
                break
        
        if not bookmarks_path:
            raise FileNotFoundError("Brave bookmarks file not found in any known location")
        
        # Parse JSON and extract URLs with titles
        with open(bookmarks_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        bookmarks = []
        # Recursively extract bookmarks from JSON structure
        def extract_bookmarks(node):
            if isinstance(node, dict):
                if "type" in node and node["type"] == "url":
                    if "url" in node and "name" in node:
                        bookmarks.append((node["name"], node["url"]))
                for value in node.values():
                    extract_bookmarks(value)
            elif isinstance(node, list):
                for item in node:
                    extract_bookmarks(item)
        
        extract_bookmarks(data)
        return bookmarks
    
    else:
        raise ValueError(f"Unsupported browser: {browser}")


def show_bookmarks_with_fuzzel(bookmarks: Union[List[Tuple[str, str]], List[str]], browser: str) -> str:
    """
    Display bookmarks using fuzzel and return selected URL.
    
    Args:
        bookmarks: Bookmarks data structure specific to the browser
        browser: Browser type to format output appropriately
    """
    # Format as "bookmark name - URL" for better readability
    input_text = "\n".join(f"{title} - {url}" for title, url in bookmarks)
    
    try:
        result = subprocess.run(
            ["fuzzel", "-d", "-p", f"Select a {browser.capitalize()} bookmark: "],
            input=input_text,
            text=True,
            capture_output=True,
            check=True
        )
        selected = result.stdout.strip()
        # Extract URL from "bookmark name - URL" format
        if selected and ' - ' in selected:
            selected = selected.split(' - ')[1]
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

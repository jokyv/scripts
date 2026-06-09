#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# ///
"""Manage web app desktop entries.

Usage:
  webapp.py add <name> <url> [icon_url]
  webapp.py remove <name>
  webapp.py list

Browser note: uses Brave --app= flag for clean app windows.
Firefox has experimental SSB (browser.ssb.enabled in about:config)
but not as reliable. Sticking with Brave for now.
"""

import subprocess
import sys
from pathlib import Path

APP_DIR = Path.home() / ".local" / "share" / "applications"
ICON_DIR = Path.home() / ".local" / "share" / "icons" / "hicolor" / "48x48" / "apps"
BROWSER = "brave"


def _desktop_id(name: str) -> str:
    return f"webapp-{name.replace(' ', '-')}"


def _desktop_path(name: str) -> Path:
    return APP_DIR / f"{_desktop_id(name)}.desktop"


def _favicon_url(domain: str) -> str:
    """Get favicon via Google's favicon service.
    Most reliable — handles Cloudflare-blocked sites."""
    return f"https://www.google.com/s2/favicons?domain={domain}&sz=64"


def _download_icon(name: str, icon_url: str) -> str:
    """Download icon, return icon name or fallback."""
    import urllib.request

    dest = ICON_DIR / f"{_desktop_id(name)}.png"
    try:
        urllib.request.urlretrieve(icon_url, dest)
        if dest.stat().st_size > 100:
            return _desktop_id(name)
        dest.unlink(missing_ok=True)
    except Exception:
        pass
    return BROWSER


def _update_db() -> None:
    try:
        subprocess.run(["update-desktop-database", str(APP_DIR)], capture_output=True, timeout=5)
    except FileNotFoundError:
        pass  # update-desktop-database not in PATH, non-critical


def cmd_add(name: str, url: str, icon_url: str | None = None) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    ICON_DIR.mkdir(parents=True, exist_ok=True)

    # Auto-fetch favicon via Google if no icon URL given
    if icon_url is None:
        from urllib.parse import urlparse

        domain = urlparse(url).netloc
        icon_url = _favicon_url(domain)

    icon = _download_icon(name, icon_url)

    desktop = _desktop_path(name)
    desktop.write_text(
        f"""[Desktop Entry]
Version=1.0
Name={name}
Comment={name} - Web App
Exec={BROWSER} --app={url}
Terminal=false
Type=Application
Icon={icon}
Categories=Network;Web;
StartupWMClass={_desktop_id(name)}
MimeType=
"""
    )
    desktop.chmod(0o755)
    _update_db()
    print(f"✓ Created: {name} ({url})")


def cmd_remove(name: str) -> None:
    desktop = _desktop_path(name)
    if not desktop.exists():
        print(f"No web app found: {name}")
        sys.exit(1)

    # Remove desktop entry and any icon files
    desktop.unlink()
    for ext in (".png", ".svg"):
        (ICON_DIR / f"{_desktop_id(name)}{ext}").unlink(missing_ok=True)
    _update_db()
    print(f"✓ Removed: {name}")


def cmd_list() -> None:
    entries = sorted(APP_DIR.glob("webapp-*.desktop"))
    if not entries:
        print("No web apps installed.")
        return

    print(f"{'NAME':25s} {'URL'}")
    print(f"{'----':25s} {'---'}")
    for p in entries:
        lines = p.read_text().splitlines()
        name = next((l.split("=", 1)[1] for l in lines if l.startswith("Name=")), "?")
        exec_line = next((l.split("=", 1)[1] for l in lines if l.startswith("Exec=")), "")
        url = exec_line.split("--app=", 1)[1] if "--app=" in exec_line else exec_line
        print(f"{name:25s} {url}")


def main() -> None:
    args = sys.argv[1:]

    match args:
        case ["add", name, url]:
            cmd_add(name, url)
        case ["add", name, url, icon_url]:
            cmd_add(name, url, icon_url)
        case ["remove", name]:
            cmd_remove(name)
        case ["list"]:
            cmd_list()
        case _:
            print(__doc__.strip())
            sys.exit(1)


if __name__ == "__main__":
    main()

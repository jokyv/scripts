#!/usr/bin/env python3

"""
Monitor package versions in main nixpkgs input.

A Python script for tracking package versions in your flake's main nixpkgs
input. Compares installed versions against latest available versions.
"""

import argparse
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import tomllib
from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TaskProgressColumn, TextColumn
from rich.table import Table

# ===============================================
# Variables
# ===============================================

DEFAULT_FLAKE_PATH = "flake.nix"
CACHE_TTL_HOURS = 1  # Cache time-to-live in hours

# ===============================================
# Configuration & Constants
# ===============================================


@dataclass
class Config:
    """
    Configuration for flake-freshness script.

    Attributes
    ----------
    colors : dict[str, str]
        ANSI color codes for terminal output
    cache : Dict[str, int]
        Cache configuration including TTL
    defaults : Dict[str, str]
        Default values for script parameters

    """

    colors: dict[str, str] = None
    cache: dict[str, int] = None
    defaults: dict[str, str] = None

    def __post_init__(self):
        if self.colors is None:
            self.colors = {
                "outdated_bg": "\033[1;31m",
                "latest_bg": "\033[1;32m",
                "equal": "\033[32m",
                "warning": "\033[33m",
                "error": "\033[31m",
                "info": "\033[34m",
                "accent": "\033[36m",
                "reset": "\033[0m",
            }
        if self.cache is None:
            self.cache = {"ttl": CACHE_TTL_HOURS * 3600}  # Convert hours to seconds
        if self.defaults is None:
            self.defaults = {"flake": "flake.nix"}


CONFIG = Config()


# Runtime paths that depend on environment
def get_cache_dir() -> Path:
    """
    Get cache directory path.

    Returns
    -------
    Path
        Path to cache directory in user's home

    """
    return Path.home() / ".cache" / "nix-flake-health"


def get_default_package_paths() -> list[Path]:
    """
    Get default package config file paths.

    Returns
    -------
    list[Path]
        List of potential config file locations

    """
    script_dir = Path(__file__).parent
    return [
        script_dir / "apps.toml",  # Bundled config
        Path("apps.toml"),  # Override in current directory
        Path.home() / ".config" / "nix-flake-health" / "apps.toml",  # User-level config
    ]


# ===============================================
# Helper Functions
# ===============================================


def run_command(cmd: list[str], capture_output: bool = True) -> tuple[int, str, str]:
    """
    Run a command and return exit code, stdout, stderr.

    Parameters
    ----------
    cmd : List[str]
        Command and arguments to execute
    capture_output : bool, optional
        Whether to capture command output, by default True

    Returns
    -------
    Tuple[int, str, str]
        Exit code, stdout, and stderr from command execution

    """
    try:
        result = subprocess.run(cmd, capture_output=capture_output, text=True)
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)


def get_current_system() -> str:
    """
    Detect current system architecture.

    Returns
    -------
    str
        System architecture string (e.g., 'x86_64-linux')

    """
    exit_code, stdout, stderr = run_command(["nix", "eval", "--impure", "--expr", "builtins.currentSystem", "--raw"])
    if exit_code == 0:
        return stdout.strip()
    else:
        print(f"{CONFIG.colors['error']}Error getting current system: {stderr}{CONFIG.colors['reset']}")
        return "x86_64-linux"  # fallback


def find_packages_config(override: str | None = None) -> Path:
    """
    Find packages config file.

    Parameters
    ----------
    override : Optional[str], optional
        Override path to config file, by default None

    Returns
    -------
    Path
        Path to found config file

    Raises
    ------
    FileNotFoundError
        If no config file is found

    """
    if override and override != "":
        config_path = Path(override)
        if config_path.exists():
            return config_path
        else:
            raise FileNotFoundError(f"Packages config not found: {override}")

    for path in get_default_package_paths():
        if path.exists():
            return path

    raise FileNotFoundError(
        "No config found. Create apps.toml in the script directory, your project root, or ~/.config/nix-flake-health/apps.toml"
    )


def extract_branch_from_url(url: str) -> str:
    """
    Extract branch name from flake URL.

    Parameters
    ----------
    url : str
        Flake URL string

    Returns
    -------
    str
        Branch name or 'unknown'

    """
    if not url:
        return "unknown"

    # Handle GitHub URLs with branches
    if "github:" in url and "/" in url:
        parts = url.split("/")
        if len(parts) > 1:
            # Extract branch from last part (e.g., nixos-unstable)
            branch_part = parts[-1]
            # Remove any query parameters or fragments
            return branch_part.split("?")[0].split("#")[0]

    return "unknown"


def extract_nixpkgs_info(flake_path: Path) -> dict:
    """
    Extract main nixpkgs branch, locked revision, and last modified date.

    Parameters
    ----------
    flake_path : Path
        Absolute path to flake.nix file

    Returns
    -------
    Dict
        Dictionary with 'branch', 'locked_rev', and 'last_modified' keys

    """
    # Change to the directory containing the flake.nix file
    original_cwd = Path.cwd()
    flake_dir = flake_path.parent

    try:
        # Change to flake directory so nix commands work correctly
        os.chdir(flake_dir)

        # Get flake metadata
        exit_code, stdout, stderr = run_command(["nix", "flake", "metadata", "--json"], capture_output=True)

        if exit_code != 0:
            print(f"{CONFIG.colors['error']}Error getting flake metadata: {stderr}{CONFIG.colors['reset']}")
            return {"branch": "nixos-unstable", "locked_rev": None, "last_modified": None}

        try:
            metadata = json.loads(stdout)
            nixpkgs_lock = metadata.get("locks", {}).get("nodes", {}).get("nixpkgs", {})
            locked_rev = nixpkgs_lock.get("locked", {}).get("rev")

            # Extract branch from URL
            url = nixpkgs_lock.get("locked", {}).get("url", "")
            branch = extract_branch_from_url(url) if url else "nixos-unstable"

            # Extract last modified timestamp
            last_modified = nixpkgs_lock.get("locked", {}).get("lastModified")

            return {"branch": branch, "locked_rev": locked_rev, "last_modified": last_modified}

        except (json.JSONDecodeError, KeyError):
            return {"branch": "nixos-unstable", "locked_rev": None, "last_modified": None}

    finally:
        # Always return to original directory
        os.chdir(original_cwd)


def load_packages(config_path: Path) -> list[str]:
    """
    Load simple package list from TOML.

    Parameters
    ----------
    config_path : Path
        Path to freshness.toml config file

    Returns
    -------
    List[str]
        List of package names

    Raises
    ------
    ValueError
        If config file doesn't contain [packages] section or has invalid format

    """
    with open(config_path, "rb") as f:
        config = tomllib.load(f)

    if "packages" not in config:
        raise ValueError("apps.toml must contain a [packages] section")

    packages = config["packages"].get("packages", [])

    # Validate packages
    if not isinstance(packages, list):
        raise ValueError("packages must be a list")

    if not packages:
        raise ValueError("packages list is empty")

    # Validate each package name
    for pkg in packages:
        if not isinstance(pkg, str):
            raise ValueError(f"Invalid package entry: {pkg} (must be a string)")
        if not pkg or pkg.strip() == "":
            raise ValueError("Package name cannot be empty")

    return packages


def get_cache_path(key: str) -> Path:
    """
    Get cache file path for a specific key.

    Parameters
    ----------
    key : str
        Cache key to generate path for

    Returns
    -------
    Path
        Path to cache file

    """
    safe_key = key.replace("/", "_").replace(":", "_")
    return get_cache_dir() / f"{safe_key}.json"


def is_cache_valid(cache_path: Path) -> bool:
    """
    Check if cache is valid.

    Parameters
    ----------
    cache_path : Path
        Path to cache file

    Returns
    -------
    bool
        True if cache exists and is not expired

    """
    if not cache_path.exists():
        return False

    cache_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
    now = datetime.now()
    age = (now - cache_time).total_seconds()

    return age < CONFIG.cache["ttl"]


def read_cache(key: str) -> str | None:
    """
    Read from cache.

    Parameters
    ----------
    key : str
        Cache key to read

    Returns
    -------
    Optional[str]
        Cached value or None if not found or expired

    """
    cache_path = get_cache_path(key)

    if is_cache_valid(cache_path):
        try:
            with open(cache_path) as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    return None


def write_cache(key: str, value: str) -> None:
    """
    Write to cache.

    Parameters
    ----------
    key : str
        Cache key to write
    value : str
        Value to cache

    """
    cache_dir = get_cache_dir()
    cache_dir.mkdir(parents=True, exist_ok=True)

    cache_path = get_cache_path(key)
    with open(cache_path, "w") as f:
        json.dump(value, f)


def get_package_version(flake_ref: str, input_name: str, package: str, use_cache: bool) -> tuple[str, bool]:
    """
    Get package version from nix eval.

    Parameters
    ----------
    flake_ref : str
        Flake reference (can be local path or remote URL like github:nixos/nixpkgs/branch)
    input_name : str
        Input name within flake (e.g., legacyPackages.x86_64-linux)
    package : str
        Package name to get version for
    use_cache : bool
        Whether to use cached values

    Returns
    -------
    Tuple[str, bool]
        Package version (or 'not found' if unavailable) and whether it was from cache

    """
    cache_key = f"{flake_ref}-{input_name}-{package}"
    from_cache = False

    if use_cache:
        cached = read_cache(cache_key)
        if cached is not None:
            return cached, True

    # Use --expr with builtins.getFlake to access packages
    # This works reliably for both local paths and remote URLs
    nix_expr = f'(builtins.getFlake "{flake_ref}").{input_name}.{package}.version or "not found"'
    cmd = ["nix", "eval", "--impure", "--expr", nix_expr, "--raw"]
    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        version = stdout.strip()
    else:
        # If the nix eval command itself fails, mark as not found
        version = "not found"

    if use_cache and version != "not found":
        write_cache(cache_key, version)

    return version, from_cache


def get_batch_package_versions(
    flake_ref: str, input_name: str, packages: list[str], use_cache: bool
) -> dict[str, tuple[str, bool]]:
    """
    Get multiple package versions in a single batch command.

    Parameters
    ----------
    flake_ref : str
        Flake reference (can be local path or remote URL like github:nixos/nixpkgs/branch)
    input_name : str
        Input name within flake (e.g., legacyPackages.x86_64-linux)
    packages : List[str]
        List of package names to get versions for
    use_cache : bool
        Whether to use cached values

    Returns
    -------
    Dict[str, Tuple[str, bool]]
        Dictionary mapping package name to (version, from_cache) tuple

    """
    results = {}
    packages_to_fetch = []

    # Check cache first
    for package in packages:
        cache_key = f"{flake_ref}-{input_name}-{package}"
        if use_cache:
            cached = read_cache(cache_key)
            if cached is not None:
                results[package] = (cached, True)
                continue
        packages_to_fetch.append(package)

    # If all were cached, return early
    if not packages_to_fetch:
        return results

    # Build nix expression to get all versions at once
    # Build attribute assignments for each package
    attr_parts = []
    for pkg in packages_to_fetch:
        attr_parts.append(f'"{pkg}" = pkgs.{pkg}.version or "not found"')
    attrs = "{ " + "; ".join(attr_parts) + "; }"

    # Use --expr with builtins.getFlake for reliable batch evaluation
    nix_expr = f'let pkgs = (builtins.getFlake "{flake_ref}").{input_name}; in {attrs}'
    cmd = ["nix", "eval", "--impure", "--expr", nix_expr, "--json"]
    exit_code, stdout, stderr = run_command(cmd)

    if exit_code == 0:
        try:
            versions = json.loads(stdout)
            for package in packages_to_fetch:
                version = versions.get(package, "not found")
                results[package] = (version, False)
                # Cache the result
                if use_cache and version != "not found":
                    cache_key = f"{flake_ref}-{input_name}-{package}"
                    write_cache(cache_key, version)
        except (json.JSONDecodeError, KeyError):
            # Fall back to individual checks
            for package in packages_to_fetch:
                results[package] = get_package_version(flake_ref, input_name, package, use_cache)
    else:
        # Fall back to individual checks if batch failed
        for package in packages_to_fetch:
            results[package] = get_package_version(flake_ref, input_name, package, use_cache)

    return results


def parse_version(version_str: str) -> tuple[list[int], str]:
    """
    Parse version string into comparable parts.

    Parameters
    ----------
    version_str : str
        Version string to parse

    Returns
    -------
    Tuple[List[int], str]
        Tuple of (numeric parts, remaining string)

    """
    # Extract numeric parts at the beginning
    match = re.match(r"^(\d+(?:\.\d+)*)", version_str)
    if match:
        numeric_part = match.group(1)
        numeric_parts = [int(x) for x in numeric_part.split(".")]
        remaining = version_str[len(numeric_part) :]
        return numeric_parts, remaining

    return [], version_str


def compare_versions(current: str, latest: str) -> str:
    """
    Compare two version strings using semantic versioning.

    Parameters
    ----------
    current : str
        Current version string
    latest : str
        Latest version string

    Returns
    -------
    str
        Comparison result: 'equal', 'outdated', or 'unknown'

    """
    if current == "not found" or latest == "not found":
        return "unknown"

    if current == latest:
        return "equal"

    # Try semantic version comparison
    try:
        current_parts, current_suffix = parse_version(current)
        latest_parts, latest_suffix = parse_version(latest)

        # If we have numeric parts, compare them
        if current_parts and latest_parts:
            # Pad shorter version with zeros
            max_len = max(len(current_parts), len(latest_parts))
            current_parts += [0] * (max_len - len(current_parts))
            latest_parts += [0] * (max_len - len(latest_parts))

            # Compare numeric parts
            for c, l in zip(current_parts, latest_parts):
                if c < l:
                    return "outdated"
                elif c > l:
                    return "equal"  # Current is newer than "latest"

            # If numeric parts are equal, compare suffixes
            if current_suffix != latest_suffix:
                return "outdated"

            return "equal"
    except Exception:
        # Fall back to string comparison
        pass

    # Simple fallback: if they're not equal, assume outdated
    return "outdated"


def format_version(version: str, status: str) -> str:
    """
    Format version with color.

    Parameters
    ----------
    version : str
        Version string to format
    status : str
        Status for color selection

    Returns
    -------
    str
        Formatted version string with ANSI color codes

    """
    match status:
        case "outdated":
            return f"{CONFIG.colors['outdated_bg']}{version}{CONFIG.colors['reset']}"
        case "equal":
            return f"{CONFIG.colors['equal']}{version}{CONFIG.colors['reset']}"
        case _:
            return version


def print_table(results: list[dict], revision_age: str) -> None:
    """
    Print results as a formatted table using Rich.

    Parameters
    ----------
    results : List[Dict]
        List of result dictionaries to display
    revision_age : str
        The age of the current nixpkgs revision

    """
    if not results:
        return

    # sort results: outdated first
    sorted_results = sorted(results, key=lambda x: x["status"] != "outdated")

    console = Console()
    table = Table(show_header=True, header_style="bold cyan")

    # Add columns
    table.add_column("Package", style="dim", width=20)
    table.add_column("Current", justify="right")
    table.add_column("Revision Age", justify="center")
    table.add_column("Latest", justify="right")
    table.add_column("Status", justify="center")

    # Add rows
    for row in sorted_results:
        # Determine status styling
        match row["status"]:
            case "equal":
                status_text = "[green]✓ up to date[/green]"
                current_style = "green"
            case "outdated":
                status_text = "[yellow]⚠ update available[/yellow]"
                current_style = "yellow"
            case _:
                status_text = "[red]?[/red]"
                current_style = "red"

        # Format current version with appropriate color
        current_version = f"[{current_style}]{row['current']}[/{current_style}]"

        # Format latest version - use same color as current for outdated packages
        if row["status"] == "outdated":
            latest_version = f"[{current_style}]{row['latest']}[/{current_style}]"
        else:
            latest_version = row["latest"]

        table.add_row(row["package"], current_version, revision_age, latest_version, status_text)

    # Print the table
    print("\n")
    console.print(table)


# ===============================================
# Main Logic
# ===============================================


def main(
    flake: str = DEFAULT_FLAKE_PATH,
    pkgs: str | None = None,
    updates_only: bool = False,
    no_cache: bool = False,
    json_output: bool = False,
) -> None:
    """
    Monitor package versions in main nixpkgs input.

    Parameters
    ----------
    flake : str, optional
        Path to flake.nix file, by default "flake.nix"
    pkgs : Optional[str], optional
        Path to freshness.toml config, by default None
    updates_only : bool, optional
        Only show packages with updates available, by default False
    no_cache : bool, optional
        Skip cache and force fresh lookups, by default False
    json_output : bool, optional
        Output results as JSON, by default False

    """
    # Resolve flake path to absolute path
    flake_path = Path(flake)
    if not flake_path.is_absolute():
        # If relative path, try to resolve it relative to the script location first
        script_dir = Path(__file__).parent.parent  # Go up to project root from script location
        potential_path = script_dir / flake_path
        if potential_path.exists():
            flake_path = potential_path
        else:
            # Fall back to current working directory
            flake_path = Path.cwd() / flake_path

    # Validate flake exists
    if not flake_path.exists():
        print(f"{CONFIG.colors['error']}Error: flake.nix not found at {flake_path}{CONFIG.colors['reset']}")
        print(f"{CONFIG.colors['info']}Tried: {flake_path}{CONFIG.colors['reset']}")
        return

    # Find and load packages config
    try:
        pkgs_config = find_packages_config(pkgs)
        print(f"{CONFIG.colors['info']}Loading packages from: {pkgs_config}{CONFIG.colors['reset']}")
        packages = load_packages(pkgs_config)
    except (FileNotFoundError, ValueError) as e:
        print(f"{CONFIG.colors['error']}Error: {e}{CONFIG.colors['reset']}")
        return

    if not packages:
        print(f"{CONFIG.colors['warning']}No packages found to check{CONFIG.colors['reset']}")
        return

    # Detect current system architecture
    system = get_current_system()

    print(f"{CONFIG.colors['info']}Checking {len(packages)} packages from nixpkgs...{CONFIG.colors['reset']}\n")

    # Extract nixpkgs info
    print(f"{CONFIG.colors['info']}Extracting nixpkgs info from: {flake_path}{CONFIG.colors['reset']}")
    nixpkgs_info = extract_nixpkgs_info(flake_path)

    # Calculate revision age
    revision_age_str = "N/A"
    last_modified_timestamp = nixpkgs_info.get("last_modified")
    if last_modified_timestamp:
        modified_date = datetime.fromtimestamp(last_modified_timestamp)
        age_delta = datetime.now() - modified_date
        age_days = age_delta.days
        if age_days == 0:
            revision_age_str = "today"
        elif age_days == 1:
            revision_age_str = "1 day ago"
        else:
            revision_age_str = f"{age_days} days ago"

    if not nixpkgs_info.get("locked_rev"):
        print(f"{CONFIG.colors['warning']}Warning: Could not determine locked revision{CONFIG.colors['reset']}")

    # Check each package against nixpkgs
    use_cache = not no_cache
    results = []
    cache_hits = 0
    cache_misses = 0

    # Show cache mode
    cache_mode_str = "disabled" if no_cache else "enabled"
    print(f"{CONFIG.colors['info']}Cache: {cache_mode_str}{CONFIG.colors['reset']}\n")

    # Use progress bar for visual feedback
    console = Console()
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        # Batch fetch current versions
        task = progress.add_task("[cyan]Fetching current versions...", total=2)
        current_versions = {}
        if nixpkgs_info.get("locked_rev"):
            current_versions = get_batch_package_versions(
                f"github:nixos/nixpkgs/{nixpkgs_info['locked_rev']}",
                f"legacyPackages.{system}",
                packages,
                use_cache,
            )
        else:
            # If no locked revision, mark all as "no lock"
            for package in packages:
                current_versions[package] = ("no lock", False)
        progress.advance(task)

        # Batch fetch latest versions
        progress.update(task, description="[cyan]Fetching latest versions...")
        latest_versions = get_batch_package_versions(
            f"github:nixos/nixpkgs/{nixpkgs_info['branch']}", f"legacyPackages.{system}", packages, use_cache
        )
        progress.advance(task)

        # Process results
        for package in packages:
            current, current_from_cache = current_versions.get(package, ("not found", False))
            latest, latest_from_cache = latest_versions.get(package, ("not found", False))

            # Track cache statistics
            if current_from_cache:
                cache_hits += 1
            else:
                cache_misses += 1

            if latest_from_cache:
                cache_hits += 1
            else:
                cache_misses += 1

            status = compare_versions(current, latest)

            results.append(
                {
                    "package": package,
                    "branch": nixpkgs_info["branch"],
                    "current": current,
                    "latest": latest,
                    "status": status,
                    "current_cached": current_from_cache,
                    "latest_cached": latest_from_cache,
                }
            )

    # Filter results if updates-only
    display_results = [r for r in results if r["status"] == "outdated"] if updates_only else results

    # Output results
    if json_output:
        # Add revision age to JSON output as well
        output_data = {"revision_age": revision_age_str, "packages": display_results}
        print(json.dumps(output_data, indent=2))
        return

    # Display table using Rich
    print_table(display_results, revision_age_str)

    # Summary
    outdated = [r for r in results if r["status"] == "outdated"]
    outdated_count = len(outdated)

    if outdated_count > 0:
        print(f"\n{CONFIG.colors['accent']}Summary:{CONFIG.colors['reset']}")
        print(f"  • {outdated_count} packages with updates available")
        print(f"  • Branch: {nixpkgs_info['branch']}")
        print(f"  • Current Revision Age: {revision_age_str}")

        # Show cache statistics
        if use_cache:
            total_checks = cache_hits + cache_misses
            cache_hit_rate = (cache_hits / total_checks * 100) if total_checks > 0 else 0
            print(f"  • Cache: {cache_hits} hits, {cache_misses} misses ({cache_hit_rate:.0f}% hit rate)")

        print(f"\n{CONFIG.colors['info']}Next steps:{CONFIG.colors['reset']}")
        print("  nix flake lock --update-input nixpkgs")
    else:
        print(f"\n{CONFIG.colors['equal']}✓ All packages are up to date!{CONFIG.colors['reset']}")

        # Show cache statistics
        if use_cache:
            total_checks = cache_hits + cache_misses
            cache_hit_rate = (cache_hits / total_checks * 100) if total_checks > 0 else 0
            print(f"  • Cache: {cache_hits} hits, {cache_misses} misses ({cache_hit_rate:.0f}% hit rate)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Monitor package versions in main nixpkgs input")
    parser.add_argument("--flake", default=DEFAULT_FLAKE_PATH, help="Path to flake.nix")
    parser.add_argument("--pkgs", help="Path to freshness.toml config")
    parser.add_argument("--updates-only", action="store_true", help="Only show packages with updates available")
    parser.add_argument("--no-cache", action="store_true", help="Skip cache, force fresh lookups")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    main(
        flake=args.flake, pkgs=args.pkgs, updates_only=args.updates_only, no_cache=args.no_cache, json_output=args.json
    )

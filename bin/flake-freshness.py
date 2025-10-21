#!/usr/bin/env python3
"""
flake-freshness.py: Monitor package versions across nixpkgs inputs

A Python script for tracking package versions across your flake's specialized
nixpkgs inputs. Compares installed versions against latest available versions
and highlights which inputs need updating.
"""

import json
import subprocess
import sys
from pathlib import Path
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple
import tomllib
import polars as pl
from datetime import datetime, timedelta
import os


# ============================================================================
# Configuration & Constants
# ============================================================================
@dataclass
class Config:
    """Configuration for flake-freshness script.
    
    Attributes
    ----------
    colors : Dict[str, str]
        ANSI color codes for terminal output
    cache : Dict[str, int]
        Cache configuration including TTL
    defaults : Dict[str, str]
        Default values for script parameters
    """
    colors: Dict[str, str] = None
    cache: Dict[str, int] = None
    defaults: Dict[str, str] = None
    
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
                "reset": "\033[0m"
            }
        if self.cache is None:
            self.cache = {"ttl": 3600}  # 1 hour in seconds
        if self.defaults is None:
            self.defaults = {"flake": "flake.nix"}

CONFIG = Config()

# Runtime paths that depend on environment
def get_cache_dir() -> Path:
    """Get cache directory path.
    
    Returns
    -------
    Path
        Path to cache directory in user's home
    """
    return Path.home() / ".cache" / "flake-freshness"

def get_default_package_paths() -> List[Path]:
    """Get default package config file paths.
    
    Returns
    -------
    List[Path]
        List of potential config file locations
    """
    return [
        Path("freshness.toml"),
        Path.home() / ".config" / "flake-freshness" / "freshness.toml",
        Path("scripts") / "flake-freshness" / "freshness.toml"
    ]

# ============================================================================
# Helper Functions
# ============================================================================

def run_command(cmd: List[str], capture_output: bool = True) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr.
    
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
    """Detect current system architecture.
    
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

def find_packages_config(override: Optional[str] = None) -> Path:
    """Find packages config file.
    
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

    raise FileNotFoundError("No config found. Create freshness.toml in your project root or ~/.config/flake-freshness/freshness.toml")

def extract_input_info(flake_path: Path) -> Dict[str, Dict]:
    """Extract nixpkgs input info from flake.
    
    Parameters
    ----------
    flake_path : Path
        Path to flake.nix file
        
    Returns
    -------
    Dict[str, Dict]
        Dictionary mapping input names to their branch and locked revision info
    """
    content = flake_path.read_text().strip()
    flake_dir = flake_path.parent

    # Extract branches from flake.nix
    branches = []
    for line in content.split('\n'):
        if 'pkgs-.' in line and 'url' in line and 'github:nixos/nixpkgs/' in line:
            # Simple regex-like parsing
            if 'pkgs-' in line and 'github:nixos/nixpkgs/' in line:
                try:
                    # Extract input name and branch
                    parts = line.split('pkgs-')[1].split('.url')[0]
                    branch_part = line.split('github:nixos/nixpkgs/')[1].split('"')[0]
                    branches.append({
                        "input": f"pkgs-{parts}",
                        "branch": branch_part
                    })
                except (IndexError, ValueError):
                    continue

    # Get locked revisions from flake metadata
    exit_code, stdout, stderr = run_command(["nix", "flake", "metadata", "--json"], capture_output=True)
    
    if exit_code != 0:
        print(f"{CONFIG.colors['error']}Error getting flake metadata: {stderr}{CONFIG.colors['reset']}")
        return {}

    try:
        metadata = json.loads(stdout)
        locks = metadata.get("locks", {}).get("nodes", {})
    except json.JSONDecodeError:
        return {}

    # Combine branch and locked info
    input_info = {}
    for branch in branches:
        input_name = branch["input"]
        locked_info = locks.get(input_name, {}).get("locked", {})
        locked_rev = locked_info.get("rev") if locked_info else None
        
        input_info[input_name] = {
            "branch": branch["branch"],
            "locked_rev": locked_rev
        }

    return input_info

def load_packages(config_path: Path) -> List[Dict]:
    """Load packages from TOML config.
    
    Parameters
    ----------
    config_path : Path
        Path to freshness.toml config file
        
    Returns
    -------
    List[Dict]
        List of package dictionaries with 'package' and 'input' keys
        
    Raises
    ------
    ValueError
        If config file doesn't contain [packages] section
    """
    with open(config_path, 'rb') as f:
        config = tomllib.load(f)

    if "packages" not in config:
        raise ValueError("freshness.toml must contain a [packages] section")

    packages = []
    for input_name, package_list in config["packages"].items():
        for package in package_list:
            packages.append({
                "package": package,
                "input": input_name
            })

    return packages

def get_cache_path(key: str) -> Path:
    """Get cache file path for a specific key.
    
    Parameters
    ----------
    key : str
        Cache key to generate path for
        
    Returns
    -------
    Path
        Path to cache file
    """
    safe_key = key.replace('/', '_').replace(':', '_')
    return get_cache_dir() / f"{safe_key}.json"

def is_cache_valid(cache_path: Path) -> bool:
    """Check if cache is valid.
    
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

def read_cache(key: str) -> Optional[str]:
    """Read from cache.
    
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
            with open(cache_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return None
    return None

def write_cache(key: str, value: str) -> None:
    """Write to cache.
    
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
    with open(cache_path, 'w') as f:
        json.dump(value, f)

def get_package_version(flake_ref: str, input_name: str, package: str, use_cache: bool) -> str:
    """Get package version from nix eval.
    
    Parameters
    ----------
    flake_ref : str
        Flake reference to evaluate
    input_name : str
        Input name within flake
    package : str
        Package name to get version for
    use_cache : bool
        Whether to use cached values
        
    Returns
    -------
    str
        Package version or 'not found' if unavailable
    """
    cache_key = f"{flake_ref}-{input_name}-{package}"

    if use_cache:
        cached = read_cache(cache_key)
        if cached is not None:
            return cached

    # Try to get version
    cmd = ["nix", "eval", f"{flake_ref}#{input_name}.{package}.version", "--raw"]
    exit_code, stdout, stderr = run_command(cmd)
    
    version = stdout.strip() if exit_code == 0 else "not found"

    if use_cache and version != "not found":
        write_cache(cache_key, version)

    return version

def compare_versions(current: str, latest: str) -> str:
    """Compare two version strings.
    
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
    else:
        return "outdated"

def format_version(version: str, status: str) -> str:
    """Format version with color.
    
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

def print_table(results: List[Dict]) -> None:
    """Print results as a formatted table using polars.
    
    Parameters
    ----------
    results : List[Dict]
        List of result dictionaries to display
    """
    if not results:
        return

    # Prepare data for polars DataFrame
    table_data = []
    for row in results:
        match row["status"]:
            case "equal":
                status_text = "✓ up to date"
                status_color = CONFIG.colors["equal"]
            case "outdated":
                status_text = "⚠ update available"
                status_color = CONFIG.colors["warning"]
            case _:
                status_text = "?"
                status_color = ""
        
        table_data.append({
            "package": row["package"],
            "input": row["input"], 
            "current": format_version(row["current"], row["status"]),
            "latest": f"{CONFIG.colors['latest_bg']}{row['latest']}{CONFIG.colors['reset']}" if row["status"] == "outdated" else row["latest"],
            "status": f"{status_color}{status_text}{CONFIG.colors['reset']}"
        })

    # Create polars DataFrame
    df = pl.DataFrame(table_data)
    
    # Print the table with proper formatting
    print("\n")
    print(df)

# ============================================================================
# Main Logic
# ============================================================================

def main(
    flake: str = "flake.nix",
    pkgs: Optional[str] = None,
    input_filter: Optional[str] = None,
    updates_only: bool = False,
    no_cache: bool = False,
    json_output: bool = False
) -> None:
    """Monitor package versions across nixpkgs inputs.
    
    Parameters
    ----------
    flake : str, optional
        Path to flake.nix file, by default "flake.nix"
    pkgs : Optional[str], optional
        Path to freshness.toml config, by default None
    input_filter : Optional[str], optional
        Filter by specific input name, by default None
    updates_only : bool, optional
        Only show packages with updates available, by default False
    no_cache : bool, optional
        Skip cache and force fresh lookups, by default False
    json_output : bool, optional
        Output results as JSON, by default False
    """
    
    # Validate flake exists
    flake_path = Path(flake)
    if not flake_path.exists():
        print(f"{CONFIG.colors['error']}Error: flake.nix not found at {flake}{CONFIG.colors['reset']}")
        return

    # Find and load packages config
    try:
        pkgs_config = find_packages_config(pkgs)
        print(f"{CONFIG.colors['info']}Loading packages from: {pkgs_config}{CONFIG.colors['reset']}")
        packages = load_packages(pkgs_config)
    except (FileNotFoundError, ValueError) as e:
        print(f"{CONFIG.colors['error']}Error: {e}{CONFIG.colors['reset']}")
        return

    # Extract input info from flake
    print(f"{CONFIG.colors['info']}Extracting inputs from: {flake}{CONFIG.colors['reset']}")
    input_info = extract_input_info(flake_path)

    # Filter by input if specified
    if input_filter:
        filtered_packages = [pkg for pkg in packages if pkg["input"] == input_filter]
    else:
        filtered_packages = packages

    if not filtered_packages:
        print(f"{CONFIG.colors['warning']}No packages found to check{CONFIG.colors['reset']}")
        return

    print(f"{CONFIG.colors['info']}Checking {len(filtered_packages)} packages...{CONFIG.colors['reset']}\n")

    # Get flake directory for current versions
    flake_dir = flake_path.parent

    # Detect current system architecture
    system = get_current_system()

    # Check each package
    use_cache = not no_cache
    results = []
    
    for pkg in filtered_packages:
        info = input_info.get(pkg["input"])
        
        if not info:
            print(f"{CONFIG.colors['warning']}Warning: No info found for input {pkg['input']}{CONFIG.colors['reset']}")
            continue

        print(f"  Checking {pkg['package']} from {pkg['input']}...")

        # Get current version from locked revision
        if info.get("locked_rev"):
            current = get_package_version(
                f"github:nixos/nixpkgs/{info['locked_rev']}",
                f"legacyPackages.{system}",
                pkg["package"],
                use_cache
            )
        else:
            current = "no lock"

        # Get latest version from upstream branch
        latest = get_package_version(
            f"github:nixos/nixpkgs/{info['branch']}",
            f"legacyPackages.{system}", 
            pkg["package"],
            use_cache
        )

        status = compare_versions(current, latest)

        results.append({
            "package": pkg["package"],
            "input": pkg["input"],
            "branch": info["branch"],
            "current": current,
            "latest": latest,
            "status": status
        })

    # Filter results if updates-only
    display_results = [r for r in results if r["status"] == "outdated"] if updates_only else results

    # Output results
    if json_output:
        print(json.dumps(display_results, indent=2))
        return

    # Display table
    print_table(display_results)

    # Summary
    outdated = [r for r in results if r["status"] == "outdated"]
    outdated_count = len(outdated)

    if outdated_count > 0:
        print(f"\n{CONFIG.colors['accent']}Summary:{CONFIG.colors['reset']}")
        print(f"  • {outdated_count} packages with updates available")

        inputs_to_update = list(set(r["input"] for r in outdated))
        print(f"  • Inputs to update: {', '.join(inputs_to_update)}")

        print(f"\n{CONFIG.colors['info']}Next steps:{CONFIG.colors['reset']}")
        for inp in inputs_to_update:
            print(f"  nix flake lock --update-input {inp}")
    else:
        print(f"\n{CONFIG.colors['equal']}✓ All packages are up to date!{CONFIG.colors['reset']}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor package versions across nixpkgs inputs")
    parser.add_argument("--flake", default="flake.nix", help="Path to flake.nix")
    parser.add_argument("--pkgs", help="Path to freshness.toml config")
    parser.add_argument("--input", help="Filter by specific input (e.g., pkgs-ai)")
    parser.add_argument("--updates-only", action="store_true", help="Only show packages with updates available")
    parser.add_argument("--no-cache", action="store_true", help="Skip cache, force fresh lookups")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    main(
        flake=args.flake,
        pkgs=args.pkgs,
        input_filter=args.input,
        updates_only=args.updates_only,
        no_cache=args.no_cache,
        json_output=args.json
    )

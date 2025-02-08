# scripts

This is a collection of my personal utility scripts to speed up my life!

> [!IMPORTANT]
> Scripts originally written in Bash but i have started to convert them to Python.
> I have found that Python is better when the script gets slightly more complicated.

## How this repo is organised:

Key structural notes:
- `*.util.py` files are CLI entry points using argparse
- Shared utilities live in:
  - `bash_util.sh` - Reusable Bash functions
  - `messaging.py` - Standardized terminal output formatting
- Python scripts require Python 3.10+ and the following dependencies:
  - `sops` for secret management
  - `fuzzel` for fuzzy selection interfaces
  - `wl-clipboard`/`cliphist` for clipboard handling

## Who is this for:

- NixOS (primary).
- Arch Linux (secondary, but still should work).
- MacOS (Python utilities should work, shell scripts may NOT).
- Windows (Meh!)

## Scripts:

### Core Utilities
- `fzf_util.py` - Fuzzy file workflows (selection/moving/copying/trash management)
- `git_util.py` - Automated git operations (auto-commit/pull-all/status checks)
- `linux_util.py` - System monitoring (process/kill/weather/disk checks)
- `clip_hist.py` - Clipboard history management (Wayland-compatible)

### Python Tools
- `python_sops.py` - Encrypted secrets manager with SOPS integration
- `python_pip_update.py` - Batch pip package updater using uv
- `dfn.py` - Date-formatted filenames generator
- `messaging.py` - Rich-text console output formatting

### Shell Scripts
- `bash_util.sh` - Shared bash helpers (user prompts/input validation)
- System utilities:
  - Browser bookmark launchers (`*_bookmarks.sh`)
  - Hardware/display management (`update_wall.sh`, `update_grub.sh`)
  - Session utilities (`take_screenshot.sh`, `my_logout.sh`)

### Security Tools
- `git_crypt_init.sh` - Encrypted git repository setup
- `python_sops.py` - SOPS YAML decryption/secret retrieval
- `secrets.enc.yaml` - Central secret store (credentials/API keys)

> [!NOTE]
> Installation instructions remain valid - clone repo and add `bin/` to PATH

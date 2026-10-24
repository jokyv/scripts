# Scripts

<div align="center">

**Personal utility scripts to speed up life!**

[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-NixOS%20%7C%20Arch%20%7C%20Linux-lightgrey.svg)]()

</div>

> [!IMPORTANT]
> **Transition in Progress**: Originally written in Bash, now converting to Python for better maintainability and complexity handling.

## 🚀 Quick Start

### Prerequisites

- **Python 3.14+**
- **uv** (required for the `git_util` launcher and dependency management)
- **NixOS** (primary) or **Arch Linux** (secondary)
- **Wayland** (display server)

### Installation

```bash
# Clone the repository
git clone https://github.com/jokyv/scripts.git
cd scripts

# Install runtime dependencies only
uv sync --no-dev

# OR for development (includes linting, testing tools)
uv sync --all-groups

# Add to your PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/scripts/bin:$PATH"

# Source your shell configuration
source ~/.bashrc  # or ~/.zshrc
```

Git commands use the `git_util` launcher, which selects this repository's Python environment through `uv`; no manual virtual-environment activation is needed. Keep `uv` available on the launcher's PATH. For desktop entries or shortcuts, use the absolute path to `bin/git_util`.

## 📁 Project Structure

```
scripts/
├── bin/                      # Standalone command-line tools and shared helpers
│   ├── git_util              # Git launcher; implementation is git_util.py
│   ├── python/               # Python project starter/template
│   └── ...                   # Other commands listed in the command map below
├── nix_flake_health/
│   ├── main.py               # CLI and orchestration
│   ├── versions.py           # Package-version comparison policy
│   └── apps.toml             # Default package list
├── tests/                    # Behavior tests for Git and Nix utilities
├── archived_scripts/         # Legacy/deprecated scripts
├── docs/                     # Agent guidance
├── pyproject.toml            # Dependencies and tool configuration
└── uv.lock                   # Locked Python dependencies
```

## 🛠️ Command Map

| Path                                    | Purpose                                                                            |
| --------------------------------------- | ---------------------------------------------------------------------------------- |
| `bin/git_util`                          | Recommended Git CLI launcher; runs `bin/git_util.py` in the locked uv environment. |
| `bin/git_util.py`                       | Implements Git workflows; invoke through `bin/git_util` rather than directly.      |
| `bin/fzf_util.py`                       | Fuzzy file search, move, copy, and trash workflows.                                |
| `bin/script_launcher.py`                | Find and launch executable programs with FZF.                                      |
| `bin/bookmarks.py`                      | Search and open browser bookmarks.                                                 |
| `bin/define_word.py`                    | Look up a word from the clipboard or command line.                                 |
| `bin/dfn.py`                            | Generate date-formatted filenames.                                                 |
| `bin/webapp.py`                         | Create, list, and remove Brave web-app launchers.                                  |
| `bin/linux_util.py`                     | Linux system, process, network, and weather utilities.                             |
| `bin/clip_hist.py`                      | Wayland clipboard-history actions.                                                 |
| `bin/my_logout.py`                      | Session logout/shutdown actions with Git safety checks.                            |
| `bin/take_screenshot.py`                | Capture a selected screen region.                                                  |
| `bin/update_wall.py`                    | Change wallpapers and manage the rotation loop.                                    |
| `bin/update_grub.sh`                    | Regenerate the GRUB configuration.                                                 |
| `bin/git_commit_with_gemini.py`         | Generate a commit message from staged Git changes.                                 |
| `bin/release.py`                        | Guide a tagged release and update the changelog.                                   |
| `bin/git_crypt_init.sh`                 | Initialize encrypted Git repository support.                                       |
| `bin/python_execute_script.py`          | Run a Python script only when a virtual environment is active.                     |
| `bin/python_pip_update.py`              | Update Python packages in the active environment.                                  |
| `bin/python/python_code_init.py`        | Create a Python script from the project template.                                  |
| `bin/python/python_project_template.py` | Starter template used by `python_code_init.py`.                                    |
| `bin/python_sops.py`                    | Shared SOPS decryption helper used by Git workflows.                               |
| `bin/messaging.py`                      | Shared Rich console output and logging helpers.                                    |
| `bin/bash_util.sh`                      | Shared Bash utility functions.                                                     |
| `nix_flake_health/main.py`              | Compare configured Nix package versions with nixpkgs; see `--help` for options.    |

`bin/test.py` is an older Git utility snapshot, **not** the pytest suite. I found no in-repository callers; check any personal aliases before deciding whether to archive or remove it. The actual tests live under `tests/`.

## 📋 Usage Examples

### Git Workflow Automation

```bash
# Auto-commit configured repositories
git_util -ac

# Auto-commit all repositories under ~/projects
git_util -ac --all

# Pull or show status for repositories under ~/projects
git_util -pld
git_util -std

# Audit current repo before reading code
git_util --audit

# Commit workflow with safety checks (prompts for commit message)
git_util -cw
```

The launcher resolves the project from its own location, including through symlinks, and preserves your current working directory, arguments, and exit status. It uses the locked runtime dependencies without the development group. Existing aliases or shortcuts invoking `python3 ~/scripts/bin/git_util.py` should instead invoke `~/scripts/bin/git_util`; direct execution of `git_util.py` is retired.

Bulk discovery searches nested repositories under `~/projects`; worktrees and submodules are excluded. `--all` only expands auto-commit when used with `-ac`; `-ac` alone keeps configured paths. Bulk commit/push skips repositories with files larger than 50 MB, prints a CRITICAL warning, and continues with remaining repositories.

Secret-backed paths are loaded only for configured auto-commit (`git_util -ac` without `--all`): `notes_path`, `tasks_path`, then `~/pics/wallpapers`, as before. Help, audit, discovery-based bulk commands, and current-repository commands do not invoke SOPS. `git_util -ac --all` uses discovered repositories without loading these configured paths.

Both `-ac` and `-cw` stop a repository's command chain if `git add`, `git commit`, or `git push` fails and report the failed step with Git's error. Bulk auto-commit continues with remaining repositories and summarizes each outcome. Exit status is 1 if any repository fails (including a missing configured path or failed Git status check), otherwise 0; oversized repositories remain skips in bulk mode. A failed push leaves the local commit intact; resolve the error and push it manually. `-cw` also exits 1 when its safety checks prevent the commit.

### File Management

```bash
# Find and select files with FZF
fzf_util.py -fp "search phrase"

# Move files with fuzzy selection
fzf_util.py -mf

# Go to directory with FZF
fzf_util.py -gp
```

### Clipboard Management (Wayland)

```bash
# Show clipboard history
clip_hist.py -sh

# Add highlighted text to history
clip_hist.py -ah

# Select from history and paste
clip_hist.py -sfh
```

### Web App Launchers

```bash
webapp.py add "WhatsApp Web" https://web.whatsapp.com
webapp.py list
webapp.py remove "WhatsApp Web"
```

Requires Brave and a Wayland session. Desktop entries use
`brave --ozone-platform=wayland --app=<url>` so service-based launchers such as
Noctalia work with `WAYLAND_DISPLAY` even when `DISPLAY` is absent.
Re-run `add` with the same name and URL to update an older desktop entry.

## 🧪 Development

### Code Quality

This project uses modern Python tooling:

- **`ruff`** - Linting and formatting
- **`deptry`** - Dependency analysis
- **`bandit`** - Security scanning
- **`typos`** - Spell checking
- **`pytest`** - Testing framework

### Continuous Integration

GitHub Actions runs the test suite, dependency analysis, Python formatting checks, focused lint checks for the Nix version module, and a CLI help smoke test. The broader repository-wide Ruff lint and Bandit scans still report existing findings and are not CI gates yet.

### Running Tests and Checks

```bash
# Run tests
uv run --group dev pytest -q

# Check linting and formatting without changing files
uv run --group lint ruff check bin/ tests/ nix_flake_health/
uv run --group lint ruff format --check bin/ tests/ nix_flake_health/

# Run dependency analysis
uv run --group lint deptry .

# Run security scan
uv run --group lint bandit -r bin/
```

## 🖥️ Platform Support

| Platform       | Python Scripts | Shell Scripts | Clipboard | Notes            |
| -------------- | -------------- | ------------- | --------- | ---------------- |
| **NixOS**      | ✅             | ✅            | ✅        | Primary platform |
| **Arch Linux** | ✅             | ✅            | ✅        | Fully supported  |
| **macOS**      | ✅             | ⚠️             | ❌        | Python only      |
| **Windows**    | ⚠️              | ❌            | ❌        | Limited support  |

## 📦 Dependencies

### Python Packages

- `rich` - Rich console output
- `requests` - HTTP requests
- `pyyaml` - YAML processing

### System Tools

- `fzf` - Fuzzy finder
- `fd` - Fast file finder
- `eza` - Modern ls replacement
- `wl-clipboard` - Wayland clipboard
- `cliphist` - Clipboard history
- `sops` - Secret management
- `fuzzel` - Application launcher

## 🤝 Contributing

1. Follow the existing code style
2. Add type hints and docstrings
3. Run `uv run pre-commit run --all-files` before committing
4. Update documentation as needed

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

> 💡 **Tip**: Most scripts have built-in help - use `-h` or `--help` flag for detailed usage information.

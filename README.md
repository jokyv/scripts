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
- **uv** (recommended for dependency management)
- **NixOS** (primary) or **Arch Linux** (secondary)
- **Wayland** (display server)

### Installation

```bash
# Clone the repository
git clone https://github.com/jokyv/scripts.git
cd scripts

# Install runtime dependencies only
uv sync

# OR for development (includes linting, testing tools)
uv sync --all-groups

# Add to your PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/scripts/bin:$PATH"

# Source your shell configuration
source ~/.bashrc  # or ~/.zshrc
```

## 📁 Project Structure

```
scripts/
├── bin/                      # Main executable scripts
│   ├── fzf_util.py          # Fuzzy file workflows
│   ├── git_util.py          # Git automation
│   ├── linux_util.py        # System utilities
│   ├── clip_hist.py         # Clipboard management
│   └── messaging.py         # Shared output formatting
├── archived_scripts/        # Legacy/deprecated scripts
├── nix_flake_health/        # Nix flake health checker
└── pyproject.toml           # Project configuration
```

## 🛠️ Core Utilities

### 🐍 Python Scripts

- **`fzf_util.py`** - Fuzzy file operations (find, move, copy, trash)
- **`git_util.py`** - Automated git workflows (commit, pull, status)
- **`linux_util.py`** - System monitoring (processes, weather, disk usage)
- **`clip_hist.py`** - Wayland clipboard history management
- **`python_sops.py`** - Encrypted secrets management
- **`bookmarks.py`** - Browser bookmark launcher
- **`dfn.py`** - Date-formatted filename generator

### 🔧 Shell Scripts

- **`bash_util.sh`** - Shared bash utility functions
- **`take_screenshot.sh`** - Screenshot capture utility
- **`update_wall.sh`** - Wallpaper management
- **`weather.sh`** - Weather information
- **`my_logout.sh`** - Session management

### 🔒 Security Tools

- **`git_crypt_init.sh`** - Encrypted git repository setup
- **SOPS integration** - YAML-based secret management

## 📋 Usage Examples

### Git Workflow Automation

```bash
# Auto-commit all configured repositories
git_util.py -ac

# Show status of all git directories
git_util.py -std

# Commit workflow with safety checks
git_util.py -cw "Fix: update dependencies"
```

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

## 🧪 Development

### Code Quality

This project uses modern Python tooling:

- **`ruff`** - Linting and formatting
- **`deptry`** - Dependency analysis
- **`bandit`** - Security scanning
- **`typos`** - Spell checking
- **`pytest`** - Testing framework

### Running Tests

```bash
# Run linting and formatting
uv run ruff check .
uv run ruff format .

# Run dependency analysis
uv run deptry .

# Run security scan
uv run bandit -r bin/
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

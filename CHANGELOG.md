## [0.6.0] - 2025-12-12

### 🚀 Features

- Add flake-freshness script for monitoring package versions
- Add Python version of flake-freshness script
- Disable file path display in RichHandler
- Enhance messaging script with rich UI components and CLI support
- Add nix flake health monitoring tool
- Add "error" message level as alias for "failure" in messaging module
- _(git)_ Sort git status results to show changes first
- Refactor update_wall.sh for daemonized and configurable wallpaper management
- Enhance `python_pip_update.py` with rich output and detailed summaries
- Highlight latest version in green for outdated packages
- Add auto-rotate command and configurable interval support
- _(logging)_ Add persistent file-based logging with fallback to /tmp
- Improve nix flake health checker with batch processing and better UX
- Add modern Python development tooling setup
- Add explicit project dependencies and improve deptry configuration
- Add pre-commit to dev dependencies and enhance weather utility

### 🐛 Bug Fixes

- Adjust wallpaper update interval and formatting
- Version fetching in nix_flake_health script

### 💼 Other

- Improve comment style and consistency in update_wall.sh
- Improve code formatting and readability in python_pip_update.py
- Improve logging by stripping rich markup from file logs

### 🚜 Refactor

- Remove check-age.sh script
- Migrate messaging to logging with Rich integration
- Remove unused variables and update docstrings
- Update git_util.py to use consistent messaging system
- Upgrade git_util.py with main.py style and Rich tables
- Modernize git_util.py with type hints, pathlib, and dataclass config
- Move cache TTL to global variable for easier modification
- Use cleaner caret syntax for dependency versions

### 📚 Documentation

- Standardize changelog formatting with underscores for tags
- Add comprehensive docstrings to all Python functions
- Modernize README with comprehensive documentation

### 🎨 Styling

- Reformat code for consistency
- Format logging configuration and clean up imports
- Match latest version color with current for outdated packages

### ⚙️ Miscellaneous Tasks

- Remove author attribution from script header
- Remove deprecated flake-freshness scripts
- Update app lists to check
- Update functionality for git pull for list of repos
- Improve type hints
- Apply code formatting and fix trailing whitespace

## [0.5.0] - 2025-10-06

### 🚀 Features

- Change default versioning to minor increments
- Add interactive release type selection
- Add script to check input update dates

### 🐛 Bug Fixes

- Improve error messages with exception details

### 🚜 Refactor

- Remove duplicate version print in suggest_next_version
- Improve release script prompts and numbering
- Simplify version selection in release script
- Move repo root setup into function called from main

### 📚 Documentation

- Update function docstrings to numpy style

### 🎨 Styling

- Simplify release confirmation prompt formatting

### ⚙️ Miscellaneous Tasks

- Set git repo root as working directory in release script
- _(release)_ Update changelog for v0.4.0
- Standardize subprocess call formatting
- _(release)_ Update changelog for v0.5.0

## [0.4.0] - 2025-08-31

### 🚀 Features

- _(git)_ Add script to generate commit messages with AI
- Warn about uncommitted changes in shutdown
- Add shutdown notifications
- Enable actual system shutdown in logout script
- Add Python script for browser bookmarks with flag support
- Add script to open browser bookmarks with fuzzel selection
- Format bookmarks as 'name - URL' for readability
- Enhance fuzzel UI with colored URLs and larger window
- Add archived scripts for bookmarks, calculator, and stopwatch
- Add Python implementation of app launcher using fzf
- Add release script for versioning and changelog generation

### 🐛 Bug Fixes

- Exclude .git and .gitignore in wallpaper find
- Replace nix-profile shutdown commands with systemctl
- Correct git_util invocation and disable invalid command
- Improve detection of uncommitted changes in shutdown script
- Correct shutdown logic for uncommitted changes check
- Improve browser profile detection and bookmark extraction
- Search /usr/bin and /bin separately for executable programs

### 🚜 Refactor

- Use constant theme and match-case for message validation
- Rename git-commit-ai.sh to git_commit_with_gemini.sh
- Remove ANSI color formatting from fuzzel bookmarks display
- Replace ls with fd for finding executables in launch.sh
- Consolidate script directory path in launch script
- Restrict scripts to only use $HOME/scripts/bin directory
- Rename app_launch.py to script_launcher.py

### ⚙️ Miscellaneous Tasks

- Update CHANGELOG.md with new version
- Remove old commented logout script code
- Comment out shutdown commands in my_logout.sh
- Remove unused apps and scripts, update bookmarks script
- Make app_launch.py executable
- Move launch script to archived_scripts
- _(release)_ Update changelog for v0.4.0

## [0.3.0] - 2025-04-13

### 🚀 Features

- _(python_profject_template)_ Added more notes to remember
- Add calculator and stopwatch apps with dark theme using ttkbootstrap
- Add function to create and push a GitHub repository.

### 💼 Other

- Limit git log graph output (A)

### 📚 Documentation

- Restructure README with improved script organization and documentation

## [0.2.0] - 2025-02-05

### 🚀 Features

- _(define_word.sh)_ Sample script of checking a word's meaning
- _(weather)_ Sample code for wttr.in
- _(linux_util.py)_ Add parameter `weather`
- _(define_word.sh)_ Changed parameter for `notify-send`
- _(clip_hist.sh)_ Add script to manage clipboard history
- _(my_logout.sh)_ Add uptime to the script
- _(clip_hist.sh)_ Archiving this bash script
- _(clip_hist)_ Re-creating the script in python
- _(git_util.py)_ Small wording change
- _(git_util.py)_ Small wording change
- Add delete command to clip_hist.py
- _(.gitignore)_ Update files for .gitignore
- Add large file check to auto_commit function

### 🐛 Bug Fixes

- _(my_logout.sh)_ Removed the sudo does not need it
- _(python_code_init.py)_ Fix the path of the template
- _(git_util.py)_ Fd command is now fixed
- _(git_util.py)_ Too many empty lines when print, removing some

### 🚜 Refactor

- _(python_pip_update.py)_ Grouping libraries depending of their usage
- _(clip_hist.py)_ Linting

### 📚 Documentation

- _(CHANGELOG.md)_ Updated changelog file

## [0.1.0] - 2024-12-27

### 🚀 Features

- _(util)_ Add dprint and typos configs

### 📚 Documentation

- _(README.md)_ Update docs

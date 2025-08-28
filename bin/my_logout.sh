#!/usr/bin/env bash

# System Control Script
# Provides a graphical menu for system control operations using fuzzel
# Requirements: fuzzel, swaylock, niri (Wayland compositor)

# Exit on error, undefined variables, and propagate pipe failures
# ret -euo pipefail

# NixOS specific
# SHUTDOWN_CMD=$HOME/.nix-profile/bin/shutdown
# REBOOT_CMD=$HOME/.nix-profile/bin/reboot

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for required dependencies
for cmd in fuzzel swaylock; do
    if ! command_exists "$cmd"; then
        echo "Error: Required command '$cmd' not found." >&2
        exit 1
    fi
done

# Format uptime string
format_uptime() {
    uptime | sed -e 's/^.*up /Uptime: /' \
        -e 's/ weeks\?/w/' \
        -e 's/ days\?/d/' \
        -e 's/ hours\?/h/' \
        -e 's/ minutes\?/m/' \
        -e 's/,//g' \
        -e 's/ [0-9]* user.*load average.*$//'
}

# Show confirmation dialog
confirm_action() {
    local action=$1
    echo -e "Yes\nNo" | fuzzel --prompt "Confirm $action?" \
        --dmenu | grep -q "^Yes$"
}

# Execute action with proper error handling
execute_action() {
    local cmd=$1
    if ! $cmd; then
        notify-send "Error" "Failed to execute: $cmd" -u critical
        exit 1
    fi
}

check_uncommitted_changes() {
    # Run git_util.py and capture the output to both display and detect changes
    if git_util.py --status_all_dirs 2>&1 | grep -q "repo needs a git commit"; then
        return 0  # changes exist
    else
        return 1  # no changes
    fi
}

confirm_ignore_changes() {
    echo -e "Yes\nNo" | fuzzel --prompt "Uncommitted changes exist! Shutdown anyway?" \
        --dmenu | grep -q "^Yes$"
}

# Main menu
prompt=$(format_uptime)
options="Shutdown\nReboot\nLogout\nLock\nSleep\nCancel"
selection=$(echo -e "$options" | fuzzel --prompt "$prompt - Please Make a Selection:" \
    --dmenu)

case $selection in
    Shutdown)
        if confirm_action "shutdown"; then
            if check_uncommitted_changes; then
                if confirm_ignore_changes; then
                    notify-send "Shutting down" "Performing system shutdown now" -t 1500
                    # execute_action "systemctl poweroff"
                    # echo 'shutdown 1'
                fi
            else
                notify-send "Shutting down" "Performing system shutdown now" -t 1500
                # execute_action "systemctl poweroff"
                # echo 'shutdown 2'
            fi
        else
            notify-send "Shutdown canceled" "Shutdown was canceled" -t 1500
        fi
        ;;
    Reboot)
        if confirm_action "reboot"; then
            execute_action "systemctl reboot"
        fi
        ;;
    Logout)
        if confirm_action "logout"; then
            execute_action "pkill niri"
        fi
        ;;
    Lock)
        execute_action "swaylock -f"
        ;;
    Sleep)
        if confirm_action "sleep"; then
            execute_action "systemctl suspend"
        fi
        ;;
    *)
        exit 0
        ;;
esac

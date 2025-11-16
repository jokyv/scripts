#!/usr/bin/env bash

# -----------------------------------------------
# VARIABLES
# -----------------------------------------------

# Directory where your wallpapers are stored.
WALLPAPERS_DIR="$HOME/pics/wallpapers"

# Time interval in seconds for the loop (e.g., 60*60 for 1 hour, 30*60 for 30 mins).
LOOP_INTERVAL=$((15 * 60))

# -----------------------------------------------
# FUNCTIONS
# -----------------------------------------------

# Function to change the wallpaper
# Arguments:
#   $1: wallpapers directory (optional, defaults to WALLPAPERS_DIR)
#   $2: notification type: "auto" or "manual" (optional, defaults to "manual")
change_wallpaper() {
    local wallpapers_dir="${1:-$WALLPAPERS_DIR}"
    local notification_type="${2:-manual}"

    # If first arg is "auto", treat it as notification type, not directory
    if [ "$wallpapers_dir" = "auto" ]; then
        notification_type="auto"
        wallpapers_dir="$WALLPAPERS_DIR"
    fi

    if [ ! -d "$wallpapers_dir" ]; then
        notify-send -u critical "Wallpaper Error" "Directory not found: $wallpapers_dir"
        return 1
    fi

    local wallpaper
    wallpaper=$(find "$wallpapers_dir" -type f -not -path '*/\.git/*' -not -name '.gitignore' | shuf -n1)

    if [ -z "$wallpaper" ]; then
        notify-send -u critical "Wallpaper Error" "No wallpapers found in $wallpapers_dir"
        return 1
    fi

    swww img "$wallpaper" --transition-fps 60 --transition-type any --transition-duration 3

    # Different notification based on type
    if [ "$notification_type" = "auto" ]; then
        notify-send "Wallpaper Auto-Rotated" "Now displaying: $(basename "$wallpaper")"
    else
        notify-send "Wallpaper Updated" "Now displaying: $(basename "$wallpaper")"
    fi
}

# Function for the looping daemon
run_loop() {
    local interval="${1:-$LOOP_INTERVAL}"
    while true; do
        sleep "$interval"
        change_wallpaper "auto"
    done
}

# Function to toggle the loop on and off
# Accepts optional interval in seconds. If not provided, uses LOOP_INTERVAL default.
toggle_loop() {
    local interval_seconds="$1"

    # Find if the loop is already running by looking for the specific process.
    # We use a unique argument `--loop-daemon` to identify it.
    local pid
    pid=$(pgrep -f "$0 --loop-daemon")

    if [ -n "$pid" ]; then
        # If it's running, kill the process and notify the user.
        kill "$pid"
        notify-send "Wallpaper Loop" "Stopped automatic wallpaper changing."
    else
        # If it's not running, start it in the background.
        # `nohup` ensures it keeps running after the terminal closes.
        # `&` runs it in the background.
        # We redirect stdout/stderr to /dev/null to keep it quiet.
        nohup "$0" --loop-daemon "$interval_seconds" >/dev/null 2>&1 &
        local interval_text
        if [ -n "$interval_seconds" ]; then
            local interval_minutes=$((interval_seconds / 60))
            interval_text="every $interval_minutes minutes"
        else
            interval_text="every 15 minutes (default)"
        fi
        notify-send "Wallpaper Loop" "Started automatic wallpaper changing $interval_text."
    fi
}

# -----------------------------------------------
# MAIN
# -----------------------------------------------

# Pre-execution checks for dependencies and swww-daemon
for cmd in swww notify-send pgrep; do
    if ! command -v "$cmd" &> /dev/null; then
        echo "Error: Required command '$cmd' not found." >&2
        exit 1
    fi
done

if ! pgrep -f "swww-daemon" > /dev/null 2>&1; then
    swww-daemon >/dev/null 2>&1 &
    sleep 1
fi

# Argument parsing to decide what to do
case "$1" in
    --auto-rotate)
        # Accept optional interval in minutes as second argument
        # If no interval provided, use default (15 minutes)
        if [ -n "$2" ]; then
            if [[ "$2" =~ ^[0-9]+$ ]]; then
                # Convert minutes to seconds
                interval_seconds=$((60 * $2))
                toggle_loop "$interval_seconds"
            else
                echo "Error: --auto-rotate interval must be a number (in minutes)." >&2
                echo "Usage: $0 --auto-rotate [minutes]" >&2
                exit 1
            fi
        else
            # No interval specified, use default
            toggle_loop
        fi
        ;;
    --loop-daemon)
        # This is the background process started by `toggle_loop`.
        # Accept optional interval in seconds as second argument
        run_loop "$2"
        ;;
    *)
        # Default action: change wallpaper once.
        # This allows passing a directory as an argument, e.g., ./update_wall.sh /path/to/other/pics
        change_wallpaper "$1"
        ;;
esac

exit 0

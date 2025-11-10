#!/usr/bin/env bash

# -----------------------------------------------
# VARIABLES
# -----------------------------------------------

# Directory where your wallpapers are stored.
WALLPAPERS_DIR="$HOME/pics/wallpapers"

# Time interval in seconds for the loop (e.g., 60*60 for 1 hour, 30*60 for 30 mins).
LOOP_INTERVAL=$((60 * 60))

# -----------------------------------------------
# FUNCTIONS
# -----------------------------------------------

# Function to change the wallpaper
change_wallpaper() {
    # The directory can be passed as an argument to override the default.
    local wallpapers_dir="${1:-$WALLPAPERS_DIR}"

    if [ ! -d "$wallpapers_dir" ]; then
        notify-send -u critical "Wallpaper Error" "Directory not found: $wallpapers_dir"
        return 1
    fi

    local wallpaper
    wallpaper=$(find "$wallpapers_dir" -type f -not -path '*/\.git/*' -not -name '.gitignore' -print0 | shuf -z -n1)

    if [ -z "$wallpaper" ]; then
        notify-send -u critical "Wallpaper Error" "No wallpapers found in $wallpapers_dir"
        return 1
    fi

    swww img "$wallpaper" --transition-fps 60 --transition-type any --transition-duration 3
    notify-send "Wallpaper Updated" "Now displaying: $(basename "$wallpaper")"
}

# Function for the looping daemon
run_loop() {
    while true; do
        change_wallpaper
        sleep "$LOOP_INTERVAL"
    done
}

# Function to toggle the loop on and off
toggle_loop() {
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
        nohup "$0" --loop-daemon >/dev/null 2>&1 &
        notify-send "Wallpaper Loop" "Started automatic wallpaper changing."
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

if ! pgrep -x "swww-daemon" > /dev/null; then
    swww-daemon &
    sleep 1
fi

# Argument parsing to decide what to do
case "$1" in
    --toggle-loop)
        toggle_loop
        ;;
    --loop-daemon)
        # This is the background process started by `toggle_loop`.
        run_loop
        ;;n    *)
        # Default action: change wallpaper once.
        # This allows passing a directory as an argument, e.g., `./update_wall.sh /path/to/other/pics`
        change_wallpaper "$1"
        ;;n
esac

exit 0

#!/usr/bin/env bash

notify-send "Changing theme..."

# swaybg -m fill -i $(find ~/pics/wallpapers -type f | shuf -n1) & disown

# Initialize swww if it's not already running
if ! pgrep -x "swww-daemon" > /dev/null
then
    swww-daemon &
    sleep 1
fi

# Set the wallpapers directory
WALLPAPERS_DIR="$HOME/pics/wallpapers"

# Select a random wallpaper
WALLPAPER=$(find "$WALLPAPERS_DIR" -type f | shuf -n1)

# Set the wallpaper
swww img "$WALLPAPER" --transition-fps 60 --transition-type any --transition-duration 3


# ----------------------------------------------------- 
# Wait for 1 sec
# ----------------------------------------------------- 

sleep 1

# ----------------------------------------------------- 
# Send notification
# ----------------------------------------------------- 

notify-send "Wallpaper updated to: $WALLPAPER"

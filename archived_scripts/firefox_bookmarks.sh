#!/usr/bin/env bash

# Function to get the path of the Firefox profile
get_firefox_profile() {
    profile_path=$(find ~/.mozilla/firefox -name "*.default-release" -type d | head -n 1)
    if [ -z "$profile_path" ]; then
        echo "Firefox profile not found." >&2
        exit 1
    fi
    echo "$profile_path"
}

# Get the Firefox profile path
profile_path=$(get_firefox_profile)

# Extract bookmarks from the SQLite database
bookmarks=$(sqlite3 "$profile_path/places.sqlite" "SELECT b.title, p.url FROM moz_bookmarks b JOIN moz_places p ON b.fk = p.id WHERE b.type = 1 AND b.title != '' ORDER BY b.dateAdded DESC")

# Use fuzzel to display the list and get user selection
selected=$(echo "$bookmarks" | sed 's/|/\t/' | fuzzel -d -p "Select a bookmark: " | cut -f2)

# If a bookmark was selected, open it in Firefox
if [ -n "$selected" ]; then
    firefox "$selected"
fi

#!/usr/bin/env bash

selected=$(cat ~/.config/BraveSoftware/Brave-Browser/Default/Bookmarks | grep '"url":' | awk '{print $2}' | sed 's/"//g' | fuzzel -d -p "Select a Brave Bookmark")

if [ "$selected" ]; then
    brave $selected
fi

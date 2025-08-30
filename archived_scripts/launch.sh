#!/usr/bin/env bash

sleep .15
DIR="$HOME/scripts/bin/"

# Search the scripts directory with fd
Menu="$(fd --max-depth 1 --type executable . "$DIR" --exec basename | sort -u | fzf --prompt="Which Program Would You Like To Run : " --border=rounded --margin=5% --color='fg:104,fg+:255,pointer:12,hl:255,hl+:12,header:12,prompt:255' --height 100% --reverse --header="                    PROGRAMS " --info=hidden --header-first)" 

if [ -n "$Menu" ]; then
    # Use the full path from the scripts directory
    selected_path="$DIR/$Menu"
    if [ -x "$selected_path" ]; then
        exec "$selected_path"
    else
        echo "Error: '$selected_path' is not executable or doesn't exist"
        exit 1
    fi
fi

#!/usr/bin/env bash

sleep .15
DIR="$HOME/scripts/bin/"

# Search each directory separately with fd and combine results
Menu="$( (fd --max-depth 1 --type executable . "$DIR"; fd --max-depth 1 --type executable . "$DIR2") | xargs -I {} basename {} | sort -u | fzf --prompt="Which Program Would You Like To Run : " --border=rounded --margin=5% --color='fg:104,fg+:255,pointer:12,hl:255,hl+:12,header:12,prompt:255' --height 100% --reverse --header="                    PROGRAMS " --info=hidden --header-first)" 

if [ -n "$Menu" ]; then
    # Find the full path of the selected executable
    selected_path=$(which "$Menu" 2>/dev/null)
    if [ -n "$selected_path" ]; then
        exec "$selected_path"
    else
        echo "Error: Could not find path for '$Menu'"
        exit 1
    fi
fi

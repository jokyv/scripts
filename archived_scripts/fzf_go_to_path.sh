#!/usr/bin/env bash

# find all type directories from $HOME and choose where to cd next

fzf_go_to_path() {
    local dir
    dir=$(fd -td -H -i . "$HOME" | fzf --preview 'eza --color=always --icons=always --long --all --group-directories-first --git {}')

    if [[ -n "$dir" ]]; then
        echo "$dir"
    else
        echo "No directory selected."
    fi
}

fzf_go_to_path

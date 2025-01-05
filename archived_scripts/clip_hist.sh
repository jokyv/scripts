#!/usr/bin/env bash

# Create cache directory if it doesn't exist
cache_dir="$HOME/.cache"
mkdir -p "$cache_dir"

histfile="$HOME/.cache/cliphist"
placeholder="<NEWLINE>"

highlight() {
    clip=$(wl-paste --primary)
}

output() {
    clip=$(wl-paste 2>/dev/null)
}

write() {
    [ -f "$histfile" ] || notify-send "Creating $histfile"; touch $histfile
    [ -z "$clip" ] && exit 0
    multiline=$(echo "$clip" | sed ':a;N;$!ba;s/\n/'"$placeholder"'/g')
    grep -Fxq "$multiline" "$histfile" || echo "$multiline" >> "$histfile"
    notification=$(echo \"$multiline\")
}

sel() {
    [ ! -f "$histfile" ] && touch "$histfile"
    selection=$(tac "$histfile" | fuzzel --dmenu --lines=5 --prompt="Clipboard history: ")
    [ -n "$selection" ] && echo "$selection" | sed "s/$placeholder/\n/g" | wl-copy && notification="Copied to clipboard!"
}

case "$1" in
    add) highlight && write ;;
    out) output && write ;;
    sel) sel ;;
    *) printf "$0 | File: $histfile\n\nadd - copies primary selection to clipboard, and adds to history file\nout - pipe commands to copy output to clipboard, and add to history file\nsel - select from history file with fuzzel and recopy!\n" ; exit 0 ;;
esac

[ -n "$notification" ] && notify-send -h string:fgcolor:#2e3440 "$notification"

#!/usr/bin/env bash

prompt=$(uptime | sed -e 's/^.*up /Uptime: /' \
    -e 's/ weeks\?/w/' \
    -e 's/ days\?/d/' \
    -e 's/ hours\?/h/' \
    -e 's/ minutes\?/m/' \
    -e 's/,//g' \
    -e 's/ [0-9]* user.*load average.*$//')

SRL=$(echo -e "Shutdown\nReboot\nLogout\nLock\nCancel" | fuzzel --prompt "$prompt - Please Make a Selection:" --dmenu)

case $SRL in
    Shutdown) 
        sudo $HOME/.nix-profile/bin/shutdown -h now
        ;;
    Reboot)
        sudo $HOME/.nix-profile/bin/reboot
        ;;
    Logout)
        pkill niri
        ;;
    Lock)
        swaylock
        ;;
    *)
        ;;
esac

#!/usr/bin/env bash

SRL=$(echo -e "Shutdown\nReboot\nLogout\nLock\nCancel" | fuzzel --prompt "Please Make a Selection:" --dmenu)

case $SRL in
    Shutdown) 
        # sudo /sbin/shutdown -h now
        sudo /home/jokyv/.nix-profile/bin/shutdown -h now
        ;;
    Reboot)
        sudo /home/jokyv/.nix-profile/bin/reboot
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

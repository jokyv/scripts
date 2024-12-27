#!/usr/bin/env bash

# Here all my re-usable bash functions
# If you want to use on another bash script simply do the following:
# source ~/scripts/bash_util.sh inside another .sh file
# then run the function normally as pause_for_user

# Ask the enter before continue to the next section of the script
pause_for_user() {
    echo
    echo -e "\e[1;36m----------------------------------------\e[0m"
    read -p $'\e[1;33mPress Enter to continue to the next part\e[0m'
    echo -e "\e[1;36m----------------------------------------\e[0m"
    echo
}

# a helper function when a section is of a script is 'disabled'
work_in_progress() {
  echo ""
  echo 'this section is work in progress'
  echo ""
}

# Ask Y/n
function ask() {
    read -p "$1 (Y/n): " resp
    if [ -z "$resp" ]; then
        response_lc="y" # empty is Yes
    else
        response_lc=$(echo "$resp" | tr '[:upper:]' '[:lower:]') # case insensitive
    fi

    [ "$response_lc" = "y" ]
}

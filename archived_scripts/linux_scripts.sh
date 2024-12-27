#!/usr/bin/env bash

# -----------------------------------------------
# HELPER FUNCTIONS
# -----------------------------------------------

# a helper function when a section is of a script is 'disabled'
work_in_progress() {
  echo ""
  echo 'this section is work in progress'
  echo ""
}

# -----------------------------------------------
# SMALL FUNCTIONS
# -----------------------------------------------

# a simple script that source .aliases, .bashrc and .bash_profile files
source_files() {
  clear
  echo "-- terminal cleared"
  # sourcing .bash_profile will source .bashrc which will source .aliases
  source ~/.bash_profile
}

# a simple script that combines cd with exa
cd_with_eza() {
  cd "$1" &&
  eza -hT --tree --level=2 --sort=ext;
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

# -----------------------------------------------
# Scripl that updates pacman apps and git pull all repos 
# for daily morning usage
# -----------------------------------------------

daily_updates() {
  if ask ':: ------- UPGRADE OS --------'; then
    # upgrade with pacman
    sudo pacman -Syu
  fi
  if ask ':: ------ GIT PULL ALL ------'; then
    # pull request from all git repos
    echo "-- do you want to run the 'git pull all' command? [yes/no]"
    read answer
    # reverse inequality
    if [ "$answer" != "${answer#[yesYy]}" ]; then
      echo "...YES 'git pull all' right now!"
      git_pull_all_git_dirs
    else
      echo "...NO 'git pull all' right now!"
    fi 
  fi
}

# -----------------------------------------------
# WEEKLY UPDATE SCRIPT
# -----------------------------------------------

weekly_updates() {
  if ask ':: ----- PACMAN UPDATE ------'; then
    sudo pacman -Syu
    paru -Syu
  fi

  if ask ':: ----- GIT STATUS ALL -----'; then
    git_status_all_git_dirs
  fi

  if ask ':: ------ GIT PUSH ALL ------'; then
    work_in_progress
  fi

  if ask ':: ---- UPDATE WALLPAPER ----'; then
    echo -e 'change wallpaper at least ance a week ;)'
    feh --bg-fill $(shuf -n 1 -e ~/pics/wallpapers/*)
  fi

  if ask ':: -------- CLEAN OS --------'; then
    sudo pacman -Sc
    paru -Sc
  fi

  if ask ':: ----- Remove Orphans -----'; then
    echo 'the following are pacman defined orphan programs:'
    echo 'this was run using: "sudo pacman -Qdt"'
    echo 'please remove with sudo pacman -Rns <Program>'
    sudo pacman -Qdt
    echo ''
    echo 'the following are paru defined orphan programs:'
    paru -Qdt
  fi

  if ask ':: - Python Packages Update -'; then
    # replace pip with uv
    pip_update
  fi

  # better mirror list
  # need to install reflector
  # sudo reflector -c Singapore -a 6 --sort rate --save /etc/pacman.d/mirrorlist

  if ask ':: ------ CHECK SYSTEM ------'; then
    echo '::check if any system failures'
    systemctl --failed

    echo ''
    echo '::check how big is your cache'
    echo '::remove with rm -rf .cache/*'
    cd $HOME/.cache/
    erd --layout flat --disk-usage block --no-ignore --hidden --level 1 --sort size
  

    echo ''
    echo '::check how big is your journal'
    echo '::remove with sudo journalctl --vacuum-time=2weeks'
    cd /var/log/journal
    erd --layout flat --disk-usage block --no-ignore --hidden --level 1 --sort size
  fi

  if ask ':: ------ RUSTUP UPDATE -----'; then
    rustup update
  fi

  if ask ':: ------ CARGO UPDATE ------'; then
    cargo install-update -l
    cargo install-update -a -q
  fi

  if ask ':: ------ CARGO CACHE -------'; then
    cargo cache -a
  fi

  if ask ':: --- WEEKLY GIT COMMITS ---'; then

    read -p "Do you want to commit your wallpapers and notes? " yn
      case $yn in
        [Yy]* ) 
          git_auto_commit "$HOME/pics/wallpapers/" &&
          git_auto_commit "$HOME/repos/xxx/";;
        [Nn]* ) echo "...NO "git commit" right now!";;
        * ) echo "Please answer y or n.";;
      esac
    echo ""
  fi
}

# rename files in bulk
# ----------------------------------------------------------------------------
bulk_rename() {
  # TODO: 
  # use xargs -i touch {}.png etc to rename the files

  read -t 10 -p "Enter a phrase: " phrase
  count=0
  for file in *.png; do
    mv "$file" "${phrase}_${count}.png"
    count=$((count+1))
  done
  for file in *.jpeg; do
    mv "$file" "${phrase}_${count}.jpeg"
    count=$((count+1))
  done
  for file in *.jpg; do
    mv "$file" "${phrase}_${count}.jpg"
    count=$((count+1))
  done
  for file in *.webp; do
    mv "$file" "${phrase}_${count}.webp"
    count=$((count+1))
  done
}

# typical figure for a 250GB SSD lies between 60 and 150 terabytes written
# https://www.ontrack.com/blog/2018/02/07/how-long-do-ssds-really-last/
# ----------------------------------------------------------------------------
check_driver() {
  sudo smartctl -a /dev/nvme0n1
}

# fkill - kill processes - list only the ones you can kill.
# ----------------------------------------------------------------------------
fkill() {
  local pid 
  if [ "$UID" != "0" ]; then
    pid=$(ps -f -u $UID | sed 1d | fzf -m | awk '{print $2}')
  else
    pid=$(ps -ef | sed 1d | fzf -m | awk '{print $2}')
  fi  
  if [ "x$pid" != "x" ]
  then
    echo $pid | xargs kill -${1:-9}
  fi  
}                  

# Find the weather in Singapore
# ----------------------------------------------------------------------------
weather() {
  curl -s "https://wttr.in/${1:-Serangoon}?m2F&format=v2"
}

# Find your IP address
# ----------------------------------------------------------------------------
ip-address() {
  curl -s -H "Accept: application/json" "https://ipinfo.io/${1:-}" | jq "del(.loc, .postal, .readme)"
}

# create a folder and cd into it
# ----------------------------------------------------------------------------
mkd() {
  mkdir -p $1
  cd $1
}


# find how many hours since last commit
# ----------------------------------------------------------------------------
hour_since_last_commit() {
  now=`date +%s`
  last_commit=`git log --pretty=format:'%at' -1`
  seconds_since_last_commit=$((now-last_commit))
  hour_since_last_commit=$((seconds_since_last_commit/60/60))
  echo "hours since last commit: $hour_since_last_commit"
}

# upgrade all the python libraries that are outdated
# ----------------------------------------------------------------------------
pip_update() {
  library_list=`pip list --outdated | awk 'NR>2 {print $1}'`
  length_library_list=`echo -n "$library_list" | wc -c`
  if [ $length_library_list -ge 1 ]; then
    echo "::Proceeding to upgrade the following libraries:"
    echo ""
    echo $library_list
    echo ""
    for library in $library_list; do
      echo ""
      pip install -U $library 
      echo ""
    done
  else echo "::All python libraries are up to date"
  fi
}

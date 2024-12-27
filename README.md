# scripts

This is a collection of my personal utility scripts to speed up my life!

> [!IMPORTANT]
> Scripts originally written in Bash but i have started to convert them to Python.
> I have found that Python is better when the script gets slightly more complicated.

## How this repo is organised:

- archived_scripts folder has all the old/unused scripts.
- bin has all the active/frequently used scripts.
- secrets.enc.yaml conains all my secrets and managed using [sops](https://github.com/getsops/sops)

## Who is this for:

- NixOS (primary).
- Arch Linux (secondary, but still should work).
- MacOS (*_util.py scripts should work everything else probably NOT).
- Windows (Meh!)

## How to use this repo:

### Add scripts to your path

- `git clone git@github.com:jokyv/scripts.git` into your computer.
- Add to your path the `path/to/scripts/bin/`.

### Alternatively use symlinks

- `ln -s path/to/scripts/bin/* ~/.local/bin/`
- make sure `~/.local/bin` is in your path.

## Scripts:

- Core utility CLI apps:
  - fzf_util.py CLI app with all my fzf scripts
  - git_util.py CLI app with all my git scripts
  - linux_util.py CLI app with all my general linux scripts

- Python scripts:
  - dfn.py small script to pring the date format i want into helix
  - python_pip_update.py functions to update core or all my python libraries
  - messaging.py my messaging function for pretty terminal prints

- Shell scripts:
  - *_bookmarks.sh fuzzel app for my firefox and brave bookmark launcher
  - update_wall.sh update wallpaper and send notification of the action
  - take_screenshot.sh take a screenshot
  - update_grub.sh update grub config
  - my_logout.sh fuzzel app to select logout options

- Secret scripts:
  - git_crypt_init.py commands on how to setup [git-crypt](https://github.com/AGWA/git-crypt)
  - python_sops.py functions to decrypt a sops encrypted YAML file

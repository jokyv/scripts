#!/bin/bash

# find a string in a file
# needs ripgrep
fzf_file_that_contains_phrase() {
    phrase=$1
    rg $phrase -l |
    fzf --preview "bat --style=numbers --color=always {}" |
    xargs -r $EDITOR ;
}

# find files and folders above certain MB, for example 500MB
fzf_find_big_files() {
    file_size=$1
    fd -H . $HOME --size +$file_size | fzf
}

# find empty files
fzf_empty_files() {
    fd -te -H . $HOME | fzf
}

# find all type directories from $HOME and choose where to cd next
# fd -i for enabling case-sensitive
fzf_go_to_path() {
    cd "$(fd -td -H -i . $HOME | fzf)" &&
    eza --color=always --icons=always --long --all --group-directories-first --git
}

# find all folders from $HOME and choose where to mv next
# fd -i for enabling case-sensitive
fzf_move_to_path() {
    mv -iv $(fd -tf -H -i . $HOME | fzf) $(fd -td -H . $HOME | fzf)
}

# find all folders from $HOME and choose where to cp next
# fd -i for enabling case-sensitive
fzf_copy_to_path() {
    cp -iv $(fd -tf -H -i . $HOME | fzf) $(fd -td -H . $HOME | fzf)
}

# find all files from $HOME and opens them with helix
# fd -i for enabling case-sensitive
fzf_open_file() {
    hx $(fd -tf -H -i . $HOME | sk --preview "bat --style=numbers --color=always {}")
}

# find all my scripts, choose one with fzf and open with nvim
fzf_find_my_scripts() {
    hx $(fd -tf . $HOME/dot/bin/ | fzf --preview "bat --style=numbers --color=always {}")
}

# restore trash item with trashy
fzf_restore_file_from_trash() {
    trash list |
    fzf --multi |
    awk '{$1=$1;print}' |
    rev |
    cut -d ' ' -f1 |
    rev |
    xargs trash restore --match=exact --force
}

# empty trash item with trashy
fzf_empty_file_from_trash() {
    trash list |
    fzf --multi |
    awk '{$1=$1;print}' |
    rev |
    cut -d ' ' -f1 |
    rev |
    xargs trash empty --match=exact --force
}

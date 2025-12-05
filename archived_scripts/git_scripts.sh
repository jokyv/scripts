#!/bin/bash

# Helper function that auto git commits
# ----------------------------------------------------------------------------
git_auto_commit() {

  PATHS=("$HOME/repos/xxx/")

  for path in ${PATHS[@]}
  do
  cd $path
  git pull

  echo ":: Checking for repo {$path}"

  CHANGES_EXIST="$(git status --porcelain | wc -l)"

  # if no changes then exit with code 0
  if [ "$CHANGES_EXIST" -eq 0 ]; then
    echo ":: Nothing to commit moving on..."
  else
    git add .
    git commit -q -m "auto update at: $(date +"%d-%m-%Y %H:%M:%S")"
    git push -q
    echo ":: Found changes! git add, git commit git push performed"
  fi
  done
}

# A git init template when i start a new git project
# ----------------------------------------------------------------------------
git_init_template() {
  git init
  touch .gitignore
  echo -e "*.csv\n*.pkl\n*.xlsx\n*.txt\n__pycache__" > .gitignore
  git add .gitignore
  git commit -m "git init and git add - basic git ignore file"
}

# A simple for loop that searches git directories and
# executes a git pull for each one
# ----------------------------------------------------------------------------
git_pull_all_git_dirs() {
  cd
  pids=""
  # fd dirs that have .git but exclude dirs with names nvim or .local/share
  for file in $(fd -td -HI -g .git -gE nvim -gE .local/share)
  do
    cd $file
    cd ..
    echo "git pull for $file"
    # run it as subprocess - like bash async
    git pull -q &
    pids="$pids $!"
    cd
  done

  wait $pids
}

# A simple for loop that searches the git status of all the git dirs
# except for .cache, .local/share, cargo
# ----------------------------------------------------------------------------
git_status_all_git_dirs() {
  cd
  # fd dirs that have .git but exclude dirs with names .cache or .local/share or cargo
  for file in $(fd -td -HI -g .git -gE .cache -gE .local/share -gE cargo)
  do
    cd $file
    cd ..
    git_status=$(git status -s | wc -l)
    if [ $git_status -gt 0 ]
      then
        echo ""
        echo "## $file repo needs a git commit"
        git status -sb
    fi
    cd
  done
}

# All in one git commit bash function
# git stash, git pull, git add, git commit, git push
# check if any file big size (more than 50MB) too...
# ----------------------------------------------------------------------------
git_commit_workflow() {
  FILE_SIZE=50
  # WARNING: removing git pull and git stash as i am using git push rebase
  # git stash local repo and git pull
  # echo "...git pull and git stash apply"
  # git stash --include-untracked
  # git pull -q
  # git stash apply -q
  echo "...checking if any file above $FILE_SIZE MB exist"
  # get the path to the git folder
  DIR_PATH=$(git rev-parse --show-toplevel)
  # check if big files exist before committing
  BIG_FILE="$(fd -H . "$DIR_PATH" --size +"$FILE_SIZE"MB | wc -l)"
  if [ "$BIG_FILE" -gt 0 ]; then
    echo ""
    echo "::WARNING file(s) bigger than $FILE_SIZE MB exist..."
    echo "::delete or ignore the below file(s)"
    fd -H . "$DIR_PATH" --size +"$FILE_SIZE"MB
    return
  fi
  echo "...no big files found"
  echo "...proceeding with git add, commit and push"
  # git add everything
  git add -A
  # commit change with message $1 but be quiet
  git commit -q -m "$1"
  # git push quiet mode
  git push -q
  # check git status
  echo "...below is the current git status of the repo"
  git status -sb
}

# Get a nice graph with git repo commits
# ----------------------------------------------------------------------------
git_log_graph() {
  git log --graph --abbrev-commit --decorate --format=format:'%C(bold green)%h%C(reset) - %C(bold cyan)%aD%C(reset)
%C(bold yellow)(%ar)%C(reset)%C(auto)%d%C(reset)%n''%C(white)%s%C(reset) %C(dim white)- %an%C(reset)' --all
}

# Remove files that are tracked but suppose to be git ignored
# ----------------------------------------------------------------------------
git_clean_up() {
  # Remove the files from the index (not the actual files in the working copy)
  git rm -r --cached .
  # Add these removals to the Staging Area...
  git add .
  # ...and commit them!
  git commit -m "Clean up ignored files"
  # finally do a git push
  git push
}

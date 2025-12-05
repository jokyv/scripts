#!/usr/bin/env python3

# -----------------------------------------------
# LIBRARIES
# -----------------------------------------------

import argparse
import os
import subprocess

# -----------------------------------------------
# VARIABLES
# -----------------------------------------------


# -----------------------------------------------
# FUNCTIONS
# -----------------------------------------------


def fzf_file_that_contains_phrase(phrase: str):
    """
    Find file that contains a specified phrase.

    Parameters
    ----------
    phrase : str
        phrase that you want the script to search for

    """
    rg_process = subprocess.Popen(["rg", phrase, "-l"], stdout=subprocess.PIPE)
    fzf_process = subprocess.Popen(
        ["fzf", "--preview", "bat --style=numbers --color=always {}"],
        stdin=rg_process.stdout,
        stdout=subprocess.PIPE,
    )
    rg_process.stdout.close()
    selected_file, _ = fzf_process.communicate()
    if selected_file:
        selected_file = selected_file.decode().strip()
        subprocess.run([os.environ.get("EDITOR", "vi"), selected_file])


def fzf_find_big_files(file_size):
    """
    Find big files above a certain size.

    Parameters
    ----------
    file_size : int
        the size of the files script is going to check.

    """
    fd_process = subprocess.Popen(
        ["fd", "-H", ".", os.environ["HOME"], "--size", "+" + file_size],
        stdout=subprocess.PIPE,
    )
    fzf_process = subprocess.Popen(["fzf"], stdin=fd_process.stdout, stdout=subprocess.PIPE)
    fd_process.stdout.close()
    selected_file, _ = fzf_process.communicate()
    if selected_file:
        print(selected_file.decode().strip())


def fzf_empty_files():
    """
    Find empty files.

    find files that have zero size.
    """
    fd_process = subprocess.Popen(["fd", "-te", "-H", ".", os.environ["HOME"]], stdout=subprocess.PIPE)
    fzf_process = subprocess.Popen(["fzf"], stdin=fd_process.stdout, stdout=subprocess.PIPE)
    fd_process.stdout.close()
    selected_file, _ = fzf_process.communicate()
    if selected_file:
        print(selected_file.decode().strip())


# NOTE: does NOT work due to limitation from python itself
# NOTE: using bash script for this one
def fzf_go_to_path():
    """Go to a path from a selection of folders."""
    fd_process = subprocess.Popen(["fd", "-td", "-H", "-i", ".", os.environ["HOME"]], stdout=subprocess.PIPE)
    fzf_process = subprocess.Popen(["fzf"], stdin=fd_process.stdout, stdout=subprocess.PIPE)
    fd_process.stdout.close()
    selected_path, _ = fzf_process.communicate()
    if selected_path:
        selected_path = selected_path.decode().strip()
        subprocess.run(["cd", selected_path], shell=True)
        subprocess.run(
            [
                "eza",
                "--color=always",
                "--icons=always",
                "--long",
                "--all",
                "--group-directories-first",
                "--git",
            ]
        )


def fzf_move_file_to_path():
    """Move a file selected via FZF to a path selected by FZF again."""
    fd_process = subprocess.Popen(["fd", "-tf", "-H", "-i", ".", os.environ["HOME"]], stdout=subprocess.PIPE)
    fzf_process = subprocess.Popen(["fzf"], stdin=fd_process.stdout, stdout=subprocess.PIPE)
    fd_process.stdout.close()
    selected_file, _ = fzf_process.communicate()

    if selected_file:
        destination_directory_process = subprocess.Popen(
            ["fd", "-td", "-H", ".", os.environ["HOME"]], stdout=subprocess.PIPE
        )
        selected_destination = subprocess.Popen(
            ["fzf"], stdin=destination_directory_process.stdout, stdout=subprocess.PIPE
        )
        destination_directory_process.stdout.close()
        selected_dir, _ = selected_destination.communicate()

        selected_file = selected_file.decode().strip()
        selected_dir = selected_dir.decode().strip()
        file_name = os.path.basename(selected_file)
        new_file_name = f"{selected_dir}{file_name}"
        if selected_dir:
            subprocess.run(["mv", "-iv", selected_file, new_file_name])


def fzf_copy_file_to_path():
    """Copy a file selected via FZF to a path selected by FZF again."""
    fd_process = subprocess.Popen(["fd", "-tf", "-H", "-i", ".", os.environ["HOME"]], stdout=subprocess.PIPE)
    fzf_process = subprocess.Popen(["fzf"], stdin=fd_process.stdout, stdout=subprocess.PIPE)
    fd_process.stdout.close()
    selected_file, _ = fzf_process.communicate()

    if selected_file:
        destination_directory_process = subprocess.Popen(
            ["fd", "-td", "-H", ".", os.environ["HOME"]], stdout=subprocess.PIPE
        )
        selected_destination = subprocess.Popen(
            ["fzf"], stdin=destination_directory_process.stdout, stdout=subprocess.PIPE
        )
        destination_directory_process.stdout.close()
        selected_dir, _ = selected_destination.communicate()

        selected_file = selected_file.decode().strip()
        selected_dir = selected_dir.decode().strip()
        file_name = os.path.basename(selected_file)
        new_file_name = f"{selected_dir}{file_name}"
        if selected_dir:
            subprocess.run(["cp", "-iv", selected_file, new_file_name])


def fzf_open_file_from_path():
    """Open a file selected via FZF using helix editor."""
    fd_output = subprocess.Popen(["fd", "-tf", "-H", "-i", ".", os.environ["HOME"]], stdout=subprocess.PIPE)
    selected_file = subprocess.Popen(
        ["fzf", "--preview", "bat --style=numbers --color=always {}"],
        stdin=fd_output.stdout,
        stdout=subprocess.PIPE,
    )
    fd_output.stdout.close()
    file, _ = selected_file.communicate()
    file = file.decode().strip()

    if file:
        subprocess.run(["hx", file])


def fzf_find_my_scripts():
    """Select a script from multiple script folders using FZF."""
    home = os.environ["HOME"]
    search_paths = [os.path.join(home, "scripts/bin")]
    fd_output = subprocess.Popen(["fd", "-tf", "."] + search_paths, stdout=subprocess.PIPE)

    selected_script = subprocess.Popen(
        ["fzf", "--preview", "bat --style=numbers --color=always {}"],
        stdin=fd_output.stdout,
        stdout=subprocess.PIPE,
    )
    fd_output.stdout.close()
    script, _ = selected_script.communicate()
    script = script.decode().strip()

    if script:
        subprocess.run(["hx", script])


def fzf_restore_file_from_trash():
    """Restore a file from trash."""
    trash_output = subprocess.run(["trash", "list"], capture_output=True, text=True)
    selected_files = subprocess.run(
        ["fzf", "--multi"], input=trash_output.stdout, capture_output=True, text=True
    ).stdout.strip()
    if selected_files:
        selected_files = selected_files.split("\n")
        selected_files = [file.split()[-1] for file in selected_files]
        for file in selected_files:
            subprocess.run(["trash", "restore", "--match=exact", "--force", file])


def fzf_empty_file_from_trash():
    """Permanently delete a file from trash."""
    trash_output = subprocess.run(["trash", "list"], capture_output=True, text=True)
    selected_files = subprocess.run(
        ["fzf", "--multi"], input=trash_output.stdout, capture_output=True, text=True
    ).stdout.strip()
    if selected_files:
        selected_files = selected_files.split("\n")
        selected_files = [file.split()[-1] for file in selected_files]
        for file in selected_files:
            subprocess.run(["trash", "empty", "--match=exact", "--force", file])


# -----------------------------------------------
# MAIN
# -----------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(prog="FZF Utility", description="Utility CLI for FZF custom commands")

    parser.add_argument("-fp", "--file_phrase", action="store_true")
    parser.add_argument("-bf", "--big_files", action="store_true")
    parser.add_argument("-ef", "--empty_files", action="store_true")
    # parser.add_argument("-gp", "--go_to_path", action="store_true")
    parser.add_argument("-mf", "--move_file", action="store_true")
    parser.add_argument("-cf", "--copy_file", action="store_true")
    parser.add_argument("-of", "--open_file", action="store_true")
    parser.add_argument("-fs", "--find_scripts", action="store_true")
    parser.add_argument("-rf", "--restore_file", action="store_true")
    parser.add_argument("-et", "--empty_trash", action="store_true")

    args = parser.parse_args()

    if args.file_phrase:
        phrase = input("Enter the phrase to search: ")
        fzf_file_that_contains_phrase(phrase)
    elif args.big_files:
        file_size = input("Enter the file size in MB: ")
        fzf_find_big_files(file_size)
    elif args.empty_files:
        fzf_empty_files()
    # elif args.go_to_path:
    #     fzf_go_to_path()
    elif args.move_file:
        fzf_move_file_to_path()
    elif args.copy_file:
        fzf_copy_file_to_path()
    elif args.open_file:
        fzf_open_file_from_path()
    elif args.find_scripts:
        fzf_find_my_scripts()
    elif args.restore_file:
        fzf_restore_file_from_trash()
    elif args.empty_trash:
        fzf_empty_file_from_trash()
    else:
        print("Command was NOT found")

#!/usr/bin/env python3
"""Python implementation of the app launcher using fzf."""

import os
import subprocess
import sys
from pathlib import Path
from typing import List


def find_executables(directories: List[str]) -> List[str]:
    """
    Find all executable files in the specified directories.
    
    Args:
        directories: List of directory paths to search
        
    Returns:
        List of executable filenames
    """
    executables = set()
    
    for directory in directories:
        dir_path = Path(directory)
        if dir_path.exists() and dir_path.is_dir():
            try:
                # Use fd to find executable files
                result = subprocess.run(
                    ["fd", "--max-depth", "1", "--type", "executable", "."],
                    cwd=dir_path,
                    capture_output=True,
                    text=True,
                    check=True
                )
                # Get just the filenames
                for line in result.stdout.strip().split('\n'):
                    if line:
                        executables.add(Path(line).name)
            except subprocess.CalledProcessError:
                # Fallback to using find if fd fails
                try:
                    result = subprocess.run(
                        ["find", ".", "-maxdepth", "1", "-type", "f", "-executable"],
                        cwd=dir_path,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    for line in result.stdout.strip().split('\n'):
                        if line:
                            executables.add(Path(line[2:]).name)  # Remove './' prefix
                except subprocess.CalledProcessError:
                    continue
    
    return sorted(executables)


def show_programs_with_fzf(programs: List[str]) -> str:
    """
    Display programs using fzf and return the selected program.
    
    Args:
        programs: List of program names to display
        
    Returns:
        Selected program name or empty string if nothing selected
    """
    input_text = "\n".join(programs)
    
    try:
        result = subprocess.run(
            [
                "fzf",
                "--prompt", "Which Program Would You Like To Run : ",
                "--border", "rounded",
                "--margin", "5%",
                "--color", "fg:104,fg+:255,pointer:12,hl:255,hl+:12,header:12,prompt:255",
                "--height", "100%",
                "--reverse",
                "--header", "                    PROGRAMS ",
                "--info", "hidden",
                "--header-first"
            ],
            input=input_text,
            text=True,
            capture_output=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def find_program_path(program_name: str) -> str:
    """
    Find the full path of a program using which.
    
    Args:
        program_name: Name of the program to find
        
    Returns:
        Full path to the program or empty string if not found
    """
    try:
        result = subprocess.run(
            ["which", program_name],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def main() -> None:
    """Main function to handle program selection and execution."""
    # Use only the scripts bin directory
    scripts_bin = str(Path.home() / "scripts" / "bin")
    directories = [scripts_bin]
    
    try:
        # Find all executable programs
        programs = find_executables(directories)
        
        if not programs:
            print("Error: No executable programs found", file=sys.stderr)
            sys.exit(1)
        
        # Show selection interface
        selected_program = show_programs_with_fzf(programs)
        
        if not selected_program:
            sys.exit(0)
        
        # Find the full path in the scripts bin directory
        program_path = str(Path(scripts_bin) / selected_program)
        
        if Path(program_path).is_file() and os.access(program_path, os.X_OK):
            # Use execvp to replace the current process with the selected program
            os.execvp(program_path, [program_path])
        else:
            print(f"Error: '{program_path}' is not executable or doesn't exist", file=sys.stderr)
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nOperation cancelled", file=sys.stderr)
        sys.exit(0)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

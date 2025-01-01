#!/usr/bin/env python3

import argparse
import os
import subprocess
import sys
import time

import requests

# -----------------------------------------------
# FUNCTIONS
# -----------------------------------------------


# TODO: this probably does not work in python
def source_bash_profile():
    # Clear the terminal
    subprocess.run(["clear"], shell=True)
    print("-- terminal cleared")

    # Get the path to the user's home directory
    home_dir = os.path.expanduser("~")
    bash_profile_path = os.path.join(home_dir, ".bash_profile")

    if os.path.exists(bash_profile_path):
        print(f"Sourcing {bash_profile_path}")

        # Create a new Bash session, source the .bash_profile, and run 'env'
        # to get all environment variables
        process = subprocess.Popen(
            ["bash", "-c", f"source {bash_profile_path} && env"],
            stdout=subprocess.PIPE,
            universal_newlines=True,
        )

        # Capture the output
        output, _ = process.communicate()

        # Update Python's environment with the variables from Bash
        for line in output.split("\n"):
            if "=" in line:
                key, value = line.split("=", 1)
                os.environ[key] = value

        print("Bash profile sourced successfully")
    else:
        print(f"{bash_profile_path} does not exist")


# TODO: this probably does not work in python
def cd_with_eza(directory):
    try:
        os.chdir(directory)
        subprocess.run(["eza", "-hT", "--tree", "--level=2", "--sort=ext"])
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)


# TODO: that is working!
def check_driver():
    try:
        subprocess.run(["sudo", "smartctl", "-a", "/dev/nvme0n1"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}", file=sys.stderr)


# TODO: that is working!
def fkill(signal=9):
    try:
        uid = os.getuid()
        ps_command = f"ps -f -u {uid} | sed 1d" if uid != 0 else "ps -ef | sed 1d"

        # Use fzf to filter the process list and awk to get the PID(s)
        result = subprocess.run(
            f"{ps_command} | fzf -m | awk '{{print $2}}'",
            shell=True,
            capture_output=True,
            text=True,
        )

        pids = result.stdout.strip().splitlines()

        if pids:
            subprocess.run(["kill", f"-{signal}"] + pids, check=True)
        else:
            print("No process selected.")

    except subprocess.CalledProcessError as e:
        print(f"Command failed with error: {e}", file=sys.stderr)


# TODO: that is working!
def weather(location="Serangoon"):
    try:
        url = f"https://wttr.in/{location}?m2F&format=v2"
        response = requests.get(url)
        if response.status_code == 200:
            print(response.text)
        else:
            print(f"Failed to retrieve weather data: {response.status_code}")
    except requests.RequestException as e:
        print(f"An error occurred: {e}")


# TODO: that is working!
def ip_address(ip=""):
    try:
        url = f"https://ipinfo.io/{ip}"
        headers = {"Accept": "application/json"}
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            data = response.json()
            # Remove 'loc', 'postal', and 'readme' fields
            for field in ["loc", "postal", "readme"]:
                data.pop(field, None)
            print(data)
        else:
            print(f"Failed to retrieve IP information: {response.status_code}")

    except requests.RequestException as e:
        print(f"An error occurred: {e}")


# TODO: that is NOT working
# it creates the directory but doesnt switch to it
def mkd(directory):
    try:
        os.makedirs(
            directory, exist_ok=True
        )  # Create the directory if it doesn't exist
        os.chdir(directory)  # Change to the newly created directory
        print(f"Changed directory to: {os.getcwd()}")
    except Exception as e:
        print(f"An error occurred: {e}")


def hours_since_last_commit():
    try:
        # Get the current time in seconds since the epoch
        now = int(time.time())

        # Get the last commit time in seconds since the epoch
        last_commit = subprocess.check_output(
            ["git", "log", "--pretty=format:%at", "-1"], text=True
        ).strip()

        # Calculate the difference in seconds
        seconds_since_last_commit = now - int(last_commit)

        # Convert seconds to hours
        hours_since_last_commit = seconds_since_last_commit // 3600

        print(f"Hours since last commit: {hours_since_last_commit}")

    except subprocess.CalledProcessError as e:
        print(f"An error occurred while running git command: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Linux Utility", description="Utility CLI for Linux custom commands"
    )
    parser.add_argument("-sb", "--source_bash_profile", action="store_true")
    parser.add_argument("-cdd", "--cd_with_eza", action="store_true")
    parser.add_argument("-hlc", "--hours_since_last_commit", action="store_true")
    parser.add_argument("-wth", "--weather", action="store_true")

    args = parser.parse_args()
    if args.source_bash_profile:
        source_bash_profile()
    elif args.cd_with_eza:
        cd_with_eza()
    elif args.hours_since_last_commit:
        hours_since_last_commit()
    elif args.weather:
        weather()

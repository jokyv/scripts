#!/bin/bash

# Get the diff of staged changes.
CHANGES=$(git diff --staged)

# Check if there are any changes
if [ -z "$CHANGES" ]; then
  echo "No changes to commit."
  exit 0
fi

# Construct the prompt for the Gemini CLI
PROMPT="Based on the following git diff, write a concise and descriptive commit message. Reply with ONLY the commit message text, without any extra formatting or explanation.

--- DIFF ---
$CHANGES"

# Call the Gemini CLI and capture the output
COMMIT_MSG=$(gemini -p "$PROMPT")

# Check if the commit message is empty
if [ -z "$COMMIT_MSG" ]; then
  echo "Failed to generate a commit message."
  exit 1
fi

# Perform the git commit
echo "Committing with the following message:"
echo "$COMMIT_MSG"
git commit -m "$COMMIT_MSG"

echo "Commit successful."

#!/usr/bin/env bash


# Initialize a fresh git repository (if you haven't already)
git init

# Initialize git-crypt with a new symmetric key
git-crypt init

# Export the key immediately (THIS IS IMPORTANT - save it somewhere safe)
git-crypt export-key ~/.git-crypt-key

# Create .gitattributes to specify which files to encrypt
echo "*.md filter=git-crypt diff=git-crypt" > .gitattributes

# Add and commit .gitattributes first
git add .gitattributes
git commit -m "Add gitattributes"

# Add files
git add .

# Commit everything
git commit -m "Add encrypted files"

# Test the encryption
# Lock the repository
git-crypt lock

# Try to view a file (should show encrypted content)
cat test1.md

# Unlock with your key
git-crypt unlock ~/.git-crypt-key

# View file again (should be readable now)
cat test1.md

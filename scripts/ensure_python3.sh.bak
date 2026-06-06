#!/bin/bash
# Ensure all Hermes and command center scripts use python3.
# Creates backups with .bak extension before modifying.
echo "Enforcing python3 usage..."

# Fix shebangs in .py, .sh, .bash files
find ~/hermes -type f \( -name "*.py" -o -name "*.sh" -o -name "*.bash" \) -exec grep -l "^#!.*python" {} \; | while read -r file; do
    if ! grep -q "python3" "$file"; then
        echo "Updating shebang in $file"
        sed -i.bak 's/^#!.*python$/#!/usr/bin/env python3/' "$file"
    fi
done

# Replace bare 'python ' with 'python3 ' (word-boundary aware)
# This may affect comments, but it's safe as it narrows to the command word.
find ~/hermes -type f \( -name "*.sh" -o -name "*.bash" -o -name "*.py" \) -exec grep -l "\<python " {} \; | while read -r file; do
    echo "Replacing 'python ' with 'python3 ' in $file"
    sed -i.bak 's/\<python /python3 /g' "$file"
done

echo "Enforcement complete. Backups saved as *.bak files."

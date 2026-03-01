#!/usr/bin/env bash
# Fix line endings: convert CRLF to LF for all tracked text files.
# Run this before committing to ensure consistent line endings.

set -euo pipefail

echo "Fixing line endings (CRLF -> LF)..."

# Find all tracked text files and convert CRLF to LF
git ls-files -z | while IFS= read -r -d '' file; do
  # Skip binary files and non-existent files
  if [[ ! -f "$file" ]]; then
    continue
  fi

  # Check if file is a text file (has no null bytes)
  if ! file "$file" | grep -q "text"; then
    continue
  fi

  # Convert CRLF to LF if needed
  if LC_ALL=C grep -q "$(printf '\r')" "$file" 2>/dev/null; then
    perl -pi -e 's/\r$//' "$file"
    echo "  Fixed: $file"
  fi
done

echo "Line ending fix complete."

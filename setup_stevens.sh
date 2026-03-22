#!/bin/bash

# Define the root path (Change $HOME to /home/pi if not running as pi user)
BASE_DIR="$HOME/alfred/stevens"

echo "Checking project structure in: $BASE_DIR"

# 1. Create Directories
# mkdir -p creates the directory if it doesn't exist, and does nothing if it does.
mkdir -p "$BASE_DIR/importers"
mkdir -p "$BASE_DIR/dashboard"
mkdir -p "$BASE_DIR/daily_briefing"
mkdir -p "$BASE_DIR/db_utils"

# 2. Define the list of files to create
declare -a files=(
    "importers/weather_importer.py"
    "importers/mail_importer.py"
    "importers/telegram_importer.py"
    "dashboard/app.py"
    "daily_briefing/generate_brief.py"
    "daily_briefing/send_telegram.py"
    "db_utils/init_db.py"
    "db_utils/migrate.py"
    "db_utils/inspect_db.py"
    # Optional: empty __init__.py files make importing easier later
    "importers/__init__.py"
    "dashboard/__init__.py"
    "daily_briefing/__init__.py"
    "db_utils/__init__.py"
)

# 3. Create files loop
for file in "${files[@]}"; do
    FULL_PATH="$BASE_DIR/$file"
    
    # Check if file exists (-f)
    if [ ! -f "$FULL_PATH" ]; then
        touch "$FULL_PATH"
        echo "Created: $file"
    else
        echo "Skipped (already exists): $file"
    fi
done

echo "✅ Structure set up successfully."

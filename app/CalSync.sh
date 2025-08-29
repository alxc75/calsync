#!/bin/bash

# --- START LOGGING ---
# Create a log file on your Desktop for easy access.
LOG_FILE="$HOME/Library/Application\ Support/CalSync/calsync_log.txt"
exec &> "$LOG_FILE"

# --- YOUR SCRIPT LOGIC ---
echo "Log started at $(date)"
echo "--------------------------"

# Start the app
$HOME/Applications/CalSync.app/Contents/MacOS/.calsync/bin/python $HOME/Applications/CalSync.app/Contents/MacOS/CalSync.py

echo "--------------------------"
echo "Script finished at $(date)"
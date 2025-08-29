#!/bin/bash
clear
echo """
#########################################################
            Welcome to the Calsync Installer!
########################################################
"""
ORIGIN_DIR=$PWD

# Create the app bundle
echo "Creating the app..."

mkdir -p $HOME/Applications/CalSync.app/Contents/MacOS/
mkdir -p $HOME/Applications/CalSync.app/Contents/Resources/

cp ./app/* $HOME/Applications/CalSync.app/Contents/MacOS/
mv $HOME/Applications/CalSync.app/Contents/MacOS/Info.plist $HOME/Applications/CalSync.app/Contents/
mv $HOME/Applications/CalSync.app/Contents/MacOS/AppIcon.icns $HOME/Applications/CalSync.app/Contents/Resources/
cp credentials.json $HOME/Applications/CalSync.app/Contents/MacOS/

chmod +x $HOME/Applications/CalSync.app/Contents/MacOS/CalSync.sh

# Setup the python environment
echo "Creating the python environment..."

python -m venv $HOME/Applications/CalSync.app/Contents/MacOS/.calsync
source $HOME/Applications/CalSync.app/Contents/MacOS/.calsync/bin/activate
arch -x86_64 pip install -q --upgrade pip
arch -x86_64 pip install -q -r requirements.txt
cd $HOME/Applications/CalSync.app/Contents/MacOS/
playwright install


# User setup
echo "Done. Let's set up CalSync."
read -p "Enter your Google Calendar email (prevents duplicated events): " calendar_email
read -p "Should CalSync fetch events from the current day (1), week (2) or month (3)? " frequency
# validate frequency
while [[ ! "$frequency" =~ ^[1-3]$ ]]; do
    read -p "Invalid input. Please enter 1 for day, 2 for week, or 3 for month: " frequency
done

case $frequency in
    1) frequency="day" ;;
    2) frequency="week" ;;
    3) frequency="month" ;;
esac

read -p "Should CalSync ignore any specific events? (comma + space separated. Example: Daily, Lunch): " ignore_input

# Process the ignore list
if [ -n "$ignore_input" ]; then
    # Initialize an empty array
    ignore_list=""

    # Convert comma+space separated list to proper JSON array
    IFS=', ' read -r -a ignore_items <<< "$ignore_input"

    # Process each item
    for item in "${ignore_items[@]}"; do
        if [ -n "$item" ]; then
            if [ -z "$ignore_list" ]; then
                # First item doesn't need a leading comma
                ignore_list="\"$item\""
            else
                # Add comma before additional items
                ignore_list="$ignore_list, \"$item\""
            fi
        fi
    done
else
    # Empty array if no input
    ignore_list=""
fi

mkdir -p $HOME/Library/Application\ Support/CalSync/
cat <<EOF > $HOME/Library/Application\ Support/CalSync/user.json
{
    "user_email": "$calendar_email",
    "frequency": "$frequency",
    "ignore_list": [$ignore_list]
}
EOF

echo "Now using the following configuration:"
cat $HOME/Library/Application\ Support/CalSync/user.json


# Finish
echo "CalSync has been installed successfully! You can now drag the CalSync app to your Dock for easy access."
sleep 3
open ~/Applications
# rm -rf $ORIGIN_DIR/app
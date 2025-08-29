#! /bin/bash

echo """
#####################################################
        Welcome to the Calsync Config Editor!
#####################################################
"""

CONFIG_PATH="$HOME/Library/Application Support/CalSync/user.json"

if [ -f "$CONFIG_PATH" ]; then
    : # Config file exists
else
    echo "Config file not found at $CONFIG_PATH"
    exit 1
fi

echo "What do you want to do?"
echo "1. Edit User Email"
echo "2. Edit Ignore List"
echo "3. Edit Calendar Frequency"
echo "4. Print Current Configuration"
read -p "Please enter the number of your choice: " choice

edit_user_email() {
    current_email=$(grep -o '"user_email": *"[^"]*"' "$CONFIG_PATH" | cut -d '"' -f4)
    echo "Current user email: $current_email"
    read -p "Enter new user email (leave empty to keep current): " new_email

    if [ -n "$new_email" ]; then
        # Update the email in the config file
        sed -i '' "s/\"user_email\": *\"[^\"]*\"/\"user_email\": \"$new_email\"/" "$CONFIG_PATH"
        echo "User email updated to: $new_email"
    else
        echo "No changes made to user email."
    fi
}

edit_ignore_list() {
    echo "Current ignore list:"
    grep -o '"ignore_list": *\[[^]]*\]' "$CONFIG_PATH" | sed 's/.*\[\(.*\)\]/\1/' | tr -d '"' | tr ',' '\n' | sed 's/^ */  - /'

    echo ""
    echo "Options:"
    echo "1. Add items to ignore list"
    echo "2. Remove an item from ignore list"
    echo "3. Clear entire ignore list"
    read -p "Enter your choice (1-3): " ignore_option

    case $ignore_option in
        1)
            echo "Enter words/patterns to ignore (comma + space separated, e.g. 'Daily, Weekly, Lunch'):"
            read -p "> " ignore_input

            if [ -n "$ignore_input" ]; then
                # Convert comma-separated list to array
                IFS=', ' read -r -a ignore_items <<< "$ignore_input"

                for item in "${ignore_items[@]}"; do
                    if [ -n "$item" ]; then
                        # Check if ignore_list is empty
                        if grep -q '"ignore_list": *\[\]' "$CONFIG_PATH"; then
                            # Replace empty array with new item
                            sed -i '' "s/\"ignore_list\": *\[\]/\"ignore_list\": [\"$item\"]/" "$CONFIG_PATH"
                        else
                            # Add to existing array
                            sed -i '' "s/\"ignore_list\": *\[\([^]]*\)\]/\"ignore_list\": [\1, \"$item\"]/" "$CONFIG_PATH"
                        fi
                        echo "Added '$item' to ignore list"
                    fi
                done
            fi
            ;;
        2)
            read -p "Enter calendar name to remove from ignore list: " remove_item
            if [ -n "$remove_item" ]; then
                # Remove item from array
                sed -i '' "s/\"$remove_item\", *//g" "$CONFIG_PATH"
                sed -i '' "s/, *\"$remove_item\"//g" "$CONFIG_PATH"
                sed -i '' "s/\"$remove_item\"//g" "$CONFIG_PATH"
                # Fix any JSON syntax issues from removal
                sed -i '' "s/\[\s*,/[/g" "$CONFIG_PATH"
                sed -i '' "s/,\s*\]/]/g" "$CONFIG_PATH"
                sed -i '' "s/,\s*,/,/g" "$CONFIG_PATH"
                echo "Removed '$remove_item' from ignore list"
            fi
            ;;
        3)
            # Clear ignore list
            sed -i '' 's/"ignore_list": *\[[^]]*\]/"ignore_list": []/' "$CONFIG_PATH"
            echo "Ignore list cleared"
            ;;
        *)
            echo "Invalid option"
            ;;
    esac
}

edit_frequency() {
    current_frequency=$(grep -o '"frequency": *"[^"]*"' "$CONFIG_PATH" | cut -d '"' -f4)
    echo "Current calendar frequency: $current_frequency"
    echo "Available options:"
    echo "1. day - Daily calendar sync"
    echo "2. week - Weekly calendar sync"
    echo "3. month - Monthly calendar sync"
    read -p "Enter your choice (1-3): " freq_option

    case $freq_option in
        1)
            sed -i '' 's/"frequency": *"[^"]*"/"frequency": "day"/' "$CONFIG_PATH"
            echo "Calendar frequency updated to: day"
            ;;
        2)
            sed -i '' 's/"frequency": *"[^"]*"/"frequency": "week"/' "$CONFIG_PATH"
            echo "Calendar frequency updated to: week"
            ;;
        3)
            sed -i '' 's/"frequency": *"[^"]*"/"frequency": "month"/' "$CONFIG_PATH"
            echo "Calendar frequency updated to: month"
            ;;
        *)
            echo "Invalid option, frequency not changed"
            ;;
    esac
}

print_config() {
    echo "Current configuration:"
    echo "---------------------"
    if command -v jq &> /dev/null; then
        # If jq is installed, use it for pretty printing
        cat "$CONFIG_PATH" | jq .
    else
        # Otherwise, use a basic formatting approach
        user_email=$(grep -o '"user_email": *"[^"]*"' "$CONFIG_PATH" | cut -d '"' -f4)
        frequency=$(grep -o '"frequency": *"[^"]*"' "$CONFIG_PATH" | cut -d '"' -f4)
        ignore_list=$(grep -o '"ignore_list": *\[[^]]*\]' "$CONFIG_PATH" | sed 's/.*\[\(.*\)\]/\1/')

        echo "User Email: $user_email"
        echo "Frequency: $frequency"
        echo "Ignore List: [$ignore_list]"
    fi
    echo "---------------------"
}

# Process user choice
case $choice in
    1)
        edit_user_email
        echo "Configuration updated successfully!"
        ;;
    2)
        edit_ignore_list
        echo "Configuration updated successfully!"
        ;;
    3)
        edit_frequency
        echo "Configuration updated successfully!"
        ;;
    4)
        print_config
        ;;
    *)
        echo "Invalid option"
        exit 1
        ;;
esac

echo "Config file location: $CONFIG_PATH"

#!/usr/bin/env bash
# Antigravity CLI Toolbar (agy-cli-toolbar) Installer for Linux / macOS
set -e

echo -e "\033[36m==================================================\033[0m"
echo -e "\033[36m   Antigravity CLI Toolbar Installer (Linux/macOS)\033[0m"
echo -e "\033[36m==================================================\033[0m"

CUSTOM_DIR="$HOME/.antigravity-custom"
TARGET_SCRIPT="$CUSTOM_DIR/statusline.py"
TARGET_CONFIG="$CUSTOM_DIR/config.json"
SETTINGS_PATH="$HOME/.gemini/antigravity-cli/settings.json"

mkdir -p "$CUSTOM_DIR"
echo -e "\033[32m[✓] Directory ready: $CUSTOM_DIR\033[0m"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [ -f "$SCRIPT_DIR/statusline.py" ]; then
    cp "$SCRIPT_DIR/statusline.py" "$TARGET_SCRIPT"
else
    curl -fsSL "https://raw.githubusercontent.com/marceloasl99/agy-cli-toolbar/main/statusline.py" -o "$TARGET_SCRIPT"
fi
chmod +x "$TARGET_SCRIPT"
echo -e "\033[32m[✓] Installed statusline script: $TARGET_SCRIPT\033[0m"

if [ ! -f "$TARGET_CONFIG" ]; then
    if [ -f "$SCRIPT_DIR/config.example.json" ]; then
        cp "$SCRIPT_DIR/config.example.json" "$TARGET_CONFIG"
    else
        curl -fsSL "https://raw.githubusercontent.com/marceloasl99/agy-cli-toolbar/main/config.example.json" -o "$TARGET_CONFIG"
    fi
    echo -e "\033[32m[✓] Created default configuration: $TARGET_CONFIG\033[0m"
fi

if [ -f "$SETTINGS_PATH" ]; then
    cp "$SETTINGS_PATH" "$SETTINGS_PATH.bak"
    echo -e "\033[32m[✓] Created backup: $SETTINGS_PATH.bak\033[0m"
fi

echo -e "\n\033[32mInstallation completed successfully!\033[0m"
echo -e "To activate right now in your open Antigravity CLI session, run:"
echo -e "\033[33m/statusline python3 $TARGET_SCRIPT\033[0m\n"

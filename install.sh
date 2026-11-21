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

for s in statusline.py profile_manager.py oauth_auth.py; do
    if [ -f "$SCRIPT_DIR/$s" ]; then
        cp "$SCRIPT_DIR/$s" "$CUSTOM_DIR/$s"
    else
        curl -fsSL "https://raw.githubusercontent.com/marceloasl99/agy-cli-toolbar/main/$s" -o "$CUSTOM_DIR/$s"
    fi
    chmod +x "$CUSTOM_DIR/$s"
    echo -e "\033[32m[✓] Installed script: $CUSTOM_DIR/$s\033[0m"
done

# agy-profile symlink in /usr/local/bin or ~/.local/bin
if [ -d "$HOME/.local/bin" ]; then
    ln -sf "$CUSTOM_DIR/profile_manager.py" "$HOME/.local/bin/agy-profile"
    chmod +x "$HOME/.local/bin/agy-profile"
    echo -e "\033[32m[✓] Created agy-profile command in ~/.local/bin\033[0m"
fi

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
echo -e "Commands available:"
echo -e "  \033[33magy-profile list\033[0m              # List Google profiles & quotas"
echo -e "  \033[33magy-profile switch <name|num>\033[0m # Switch active profile"
echo -e "  \033[33magy-profile auth <name|num>\033[0m   # Authenticate with Google OAuth"
echo -e "  \033[33magy-profile create <name>\033[0m     # Create new profile\n"

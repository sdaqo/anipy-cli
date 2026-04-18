#!/data/data/com.termux/files/usr/bin/bash

# Configuration
REPO="Program-Adam/anipy-cli"
BINARY_NAME="anipy-cli"

echo "[*] Cleaning up old versions..."
# Remove old alias attempts to prevent conflicts
sed -i '/alias anipy-cli=/d' "$HOME/.bashrc" 2>/dev/null
sed -i '/alias anipy-cli=/d' "$HOME/.zshrc" 2>/dev/null

echo "[*] Detecting system architecture..."
OS="$(uname -s)"
ARCH="$(uname -m)"
IS_TERMUX=$(if [ -d /data/data/com.termux ]; then echo "true"; else echo "false"; fi)

# Default settings
EXT=".pyz"
PLATFORM=""

if [ "$IS_TERMUX" = "true" ]; then
    PLATFORM="termux"
    INSTALL_DIR="$PREFIX/bin"
    echo "Environment: Termux (x64/ARM) detected"
else
    INSTALL_DIR="/usr/local/bin"
    case "$OS" in
        Linux*)
            case "$ARCH" in
                x86_64)  PLATFORM="linux-x64" ;;
                aarch64|armv7l) PLATFORM="linux-arm" ;;
                *) echo "Unsupported Linux architecture: $ARCH"; exit 1 ;;
            esac
            ;;
        MSYS*|MINGW*|CYGWIN*)
            EXT=".exe"
            INSTALL_DIR="/usr/bin" 
            case "$ARCH" in
                x86_64) PLATFORM="windows-x64" ;;
                aarch64) PLATFORM="windows-arm" ;;
                *) echo "Unsupported Windows architecture: $ARCH"; exit 1 ;;
            esac
            ;;
        *) echo "Unsupported OS: $OS"; exit 1 ;;
    esac
fi

TARGET_NAME="${BINARY_NAME}${EXT}"
FULL_INSTALL_PATH="$INSTALL_DIR/$TARGET_NAME"
WRAPPER_PATH="$INSTALL_DIR/${BINARY_NAME}"

# Clean up existing files
rm -f "$FULL_INSTALL_PATH"
rm -f "$WRAPPER_PATH"

FILE_NAME="${BINARY_NAME}-${PLATFORM}${EXT}"
URL="https://github.com/${REPO}/releases/latest/download/${FILE_NAME}"

echo "[*] Downloading: ${FILE_NAME}..."
curl -L -o "./$TARGET_NAME" "$URL"

if [ $? -eq 0 ]; then
    chmod +x "./$TARGET_NAME"
    
    if [ "$IS_TERMUX" = "true" ] || [[ "$OS" == MSYS* ]]; then
        mv -f "./$TARGET_NAME" "$FULL_INSTALL_PATH"
    else
        sudo mv -f "./$TARGET_NAME" "$FULL_INSTALL_PATH"
    fi
else
    echo "[!] Download failed."; exit 1
fi

# --- FIX: CREATE WRAPPER INSTEAD OF ALIAS ---
echo "[*] Creating executable wrapper..."
if [ "$IS_TERMUX" = "true" ]; then
    cat << EOF > "$WRAPPER_PATH"
#!/data/data/com.termux/files/usr/bin/bash
python "$FULL_INSTALL_PATH" "\$@"
EOF
else
    # For standard Linux
    cat << EOF | sudo tee "$WRAPPER_PATH" > /dev/null
#!/bin/bash
python3 "$FULL_INSTALL_PATH" "\$@"
EOF
fi

chmod +x "$WRAPPER_PATH"

# --- MPV ANDROID SHIM SECTION ---
if [ "$IS_TERMUX" = "true" ]; then
    echo "[*] Setting up MPV Android Player Shim..."
    
    # Remove local mpv pkg if it exists to avoid conflict with shim
    if command -v mpv &> /dev/null && [ ! -L "$(command -v mpv)" ]; then
        pkg uninstall mpv -y
    fi

    SHIM_PATH="$PREFIX/bin/mpv"
    cat << 'SHIM' > "$SHIM_PATH"
#!/data/data/com.termux/files/usr/bin/bash
am start --user 0 -a android.intent.action.VIEW -d "$1" -n is.xyz.mpv/.MPVActivity > /dev/null 2>&1
SHIM
    chmod +x "$SHIM_PATH"

    # Configure anipy-cli to use the shim
    CONFIG_DIR="$HOME/.config/anipy-cli"
    mkdir -p "$CONFIG_DIR"
    echo -e "player: mpv\nplayer_path: mpv" > "$CONFIG_DIR/config.yaml"
fi

echo "------------------------------------------"
echo "Successfully installed anipy-cli!"
echo "You can now run it by simply typing: anipy-cli"
echo "------------------------------------------"
#!/bin/bash -e
################################################################################
#
# Cloudflare WARP GUI for linux
#
# (C) 2022, Pham Ngoc Son <phamngocsonls@gmail.com> - Public Domain
# (C) 2024, Roberto A. Foglietta <roberto.foglietta@gmail.com> - 3-clause BSD
# (C) 2025, Roberto A. Foglietta <roberto.foglietta@gmail.com> - 3-clause BSD
#
################################################################################

echo
echo "Checking system requisites and dependencies..."
echo

# Function to check if a command exists
command_exists() {
    { command -v "$1" || dpkg -l $i | grep -e "^ii"; } >/dev/null 2>&1
}

################################################################################

if [ "$HOME" == "" ]; then
    if [ "$USER" != "" -a -d "/home/$USER/" ]; then
        export HOME="/home/$USER"
         echo
         echo "WARNING: enviroment variable \$HOME is not set"
         echo "         currently set to $HOME"
         echo
         read -sp "Press a key to continue"
         echo
     fi
fi
if [ "$HOME" == "" ]; then
    echo
    echo "ERROR: enviroment variable \$HOME is not set"
    echo
    exit 1
fi

# Check for required packages
required_packages="python3-tk procps"
required_commands="pip3 python3 warp-cli dpkg xterm curl sed"
missing_packages=""

for pkg in $required_commands $required_packages; do
    if ! command_exists "$pkg"; then
        missing_packages="$missing_packages $pkg"
    fi
done

if [ -n "$missing_packages" ]; then
    echo "WARNING: The following required packages are not installed:"
    echo "$missing_packages"
    echo
    echo "Please install them using the following command:"
    echo "sudo apt-get install -y $missing_packages"
    exit 1
fi

# Check for required python modules
requirements="ipinfo requests"
if [ -n "$requirements" ]; then
    echo
    echo "Installing required Python modules: $requirements ..."
    pip3 install $requirements
    echo
fi

echo "Creating folders and copying files..."
echo

mkdir -p "$HOME/.local/share/applications/"
mkdir -p "$HOME/.local/share/icons/"
mkdir -p "$HOME/.local/bin/"

sed -e "s,%HOME%,$HOME,g" warp-gui.desktop > "$HOME/Desktop/warp-gui.desktop"

if [ -r "$HOME/.local/share/icons/warp-gui-app.png" ]; then
    # RAF: useful to trigger the image cache cleaning
    rm -f "$HOME/.local/share/icons/warp-gui-app.png"
fi

if [ -r appicon.png ]; then
    cp -f appicon.png "$HOME/.local/share/icons/warp-gui-app.png"
else
    cp -f appclue.png "$HOME/.local/share/icons/warp-gui-app.png"
fi
cp -f "$HOME/Desktop/warp-gui.desktop" "$HOME/.local/share/applications"

if [ -d warp-gui/orig/ ]; then
    cp -rf warp-gui/orig/ "$HOME/.local/bin/"
fi
cp -f warp-gui/*.py "$HOME/.local/bin/"
chmod a+x "$HOME/.local/bin/warp-gui.py"

echo "Disabling WARP taskbar applet..."
echo
systemctl --user disable --now warp-taskbar >/dev/null 2>&1 || true

echo "Installation done."
echo

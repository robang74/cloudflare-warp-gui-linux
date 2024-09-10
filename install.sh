#!/bin/bash -e
################################################################################
#
# Cloudflare WARP GUI for linux
#
# (C) 2022, Pham Ngoc Son <phamngocsonls@gmail.com> - Public Domain
# (C) 2024, Roberto A. Foglietta <roberto.foglietta@gmail.com> - 3-clause BSD
#
################################################################################

echo
echo "Checking system requisites and dependencies..."
echo

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

err=0

if [ "$HOME" == "" ]; then
    echo
    echo "ERROR: enviroment variable \$HOME is not set"
    echo
    err=1
fi

for i in pip3 python3 warp-cli dpkg; do
    if ! which $i >/dev/null; then
        echo
        echo "WARNING: $i package is not installed"
        echo
        echo "HOW2FIX: sudo apt-get install $i -y"
        echo
        err=1
    fi
done

if ! which python3 | grep -q /usr/bin/python3; then
    echo
    echo "WARNING: /usr/bin/python3 is not in execution path"
    echo
    err=1
fi

for i in python3-tk xterm curl sed procps; do
    if ! dpkg -l $i >/dev/null; then
        echo
        echo "WARNING: $i package is not installed"
        echo
        echo "HOW2FIX: sudo apt-get install $i -y"
        echo
        err=1
    fi
done

for i in ipinfo requests tkinter time os subprocess threading socket sys \
    random functools signal atexit; do
    if ! python3 -c "import $i" 2>/dev/null; then
        echo
        echo "WARNING: pip3 module which import '$i' is not installed"
        echo
        echo "HOW2FIX: pip3 install $i"
        echo
        err=1
    fi
done

if [ $err -eq 0 ]; then ########################################################

echo "Creating folders and copying files..."
echo

mkdir -p $HOME/.local/share/applications/
mkdir -p $HOME/.local/share/icons/
mkdir -p $HOME/.local/bin/

sed -e "s,%HOME%,$HOME,g" warp-gui.desktop > $HOME/Desktop/warp-gui.desktop

if [ -r $HOME/.local/share/icons/warp-gui-app.png ]; then
    # RAF: useful to trigger the image cache cleaning
    rm -f $HOME/.local/share/icons/warp-gui-app.png
fi

if [ -r appicon.png ]; then
    cp -f appicon.png $HOME/.local/share/icons/warp-gui-app.png
else
    cp -f appclue.png $HOME/.local/share/icons/warp-gui-app.png
fi
cp -f $HOME/Desktop/warp-gui.desktop $HOME/.local/share/applications

if [ -d orig/ ]; then
    cp -rf warp-gui/{orig,*.py} $HOME/.local/bin/
else
    cp -rf warp-gui/{free,*.py} $HOME/.local/bin/
fi
chmod a+x $HOME/.local/bin/warp-gui.py

echo "Disabling WARP taskbar applet..."
echo
systemctl --user disable warp-taskbar
systemctl --user stop warp-taskbar

echo "Installation done."
echo

fi #############################################################################



#!/bin/bash

set -xo pipefail

# create a simultaneous output
# pactl cannot be run as root, so we have to do sudo pactl as user pi
# and define the environment variable XDG_RUNTIME_DIR
IS_COMBINED_SINK="$(sudo -u pi env XDG_RUNTIME_DIR=/run/user/$(id -u pi) pactl list sinks | grep combined)"
if [[ -z "$IS_COMBINED_SINK" ]]; then
    sudo -u pi env XDG_RUNTIME_DIR=/run/user/$(id -u pi) pactl load-module module-combine-sink sink_name=combined
fi
sudo -u pi env XDG_RUNTIME_DIR=/run/user/$(id -u pi) pactl set-default-sink combined

# set hci0 Bluetooth interface as sink
# (!) this command needs to be executed as root
hciconfig hci0 class 0x200420

# launch BlueBox server
cd "$(dirname "$0")"
nohup ./app.py &
rm nohup.out
exit

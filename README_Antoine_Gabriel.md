#!/bin/bash

# 0) configuration initiale
# sudo apt-get update
# sudo apt-get upgrade
# sudo autoremove

# 1) intsallation de pulseaudio
sudo apt-get install pulseaudio pulseaudio-module-bluetooth
dpkg -l pulseaudio pulseaudio-module-bluetooth

# 2) brancher l'enceinte en jack

# 3) etablir la connection bluetooth
sudo bluetoothctl 
agent on
default-agent 
scan on             
pair XX:XX:XX:XX:XX:XX
connect XX:XX:XX:XX:XX:XX
exit

# 4) paprefs
sudo apt-get install paprefs
paprefs
pulseaudio -k && pulseaudio -D

# 5) pavocontrol 3.0


version_greater_than()
{
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}
# version_greater_than "$(pulseaudio --version)" 10.0 || exit 1

is_programm_installed()
{
    if ! [ -x "$(command -v $1)" ]; then
      echo 'Error: $1 is not installed.' >&2
      exit 1
    fi
}

# configuration par Antoine
# sudo apt install tightvncserver
# sudo apt-get install -y libdbus-1-dev
# pactl list short sinks
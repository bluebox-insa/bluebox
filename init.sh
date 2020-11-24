#!/bin/bash

#create a simultaneous output
pactl load-module module-combine-sink sink_name=combined
pactl set-default-sink combined
cd ~/innotech-mvp
IP_ADDR="$(hostname -I | cut -d ' ' -f 1)"
echo $IP_ADDR
flask run --host $IP_ADDR
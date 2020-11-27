#!/bin/bash

#create a simultaneous output
pactl load-module module-combine-sink sink_name=combined
pactl set-default-sink combined
cd ~/innotech-mvp
flask run --host "$(hostname -I | cut -d ' ' -f 1)"
# Configuration avec Cécile et Eloise

### 0) Configuration initiale
```bash
    # init
    $ sudo apt-get update
    $ sudo apt-get upgrade
    $ sudo apt-get autoremove
    $ sudo reboot
    
    # pulseaudio
    $ sudo apt-get install pulseaudio pulseaudio-module-bluetooth
    $ dpkg -l pulseaudio pulseaudio-module-bluetooth
    $ 
    
    # paprefs
    $ sudo apt-get install paprefs
    $ pulseaudio -k
    $ 
    
    # bluetooth
    $ bluetoothctl
    $ power on
    $ agent on
    $ default-agent
    $ 
    
    # Turn ON the bluetooth device, then
    $ scan on
    # copy the MAC adress

    # while scanning, in another terminal, we will kill Bluealsa, and start PulseAudio
    $ sudo killall bluealsa
    $ pulseaudio --start

    $ # go back to Bluetoothctl: Pair, trust and connect your device:
    $ pair xx:xx:xx:xx:xx:xx
    $ trust xx:xx:xx:xx:xx:xx
    $ connect xx:xx:xx:xx:xx:xx
    # device is connected

    # launch paprefs
    $ paprefs
    # go to tab "Simultaneous output", check box "Add virtual output device..."
    # pulseaudio -k ? ou pulseaudio -D ?
```

2.
Volume control > Configuration > passer l'enceinte en profile "AD2P Sink"
VLC > Audio > Audio output > Simultaneous output

3.
quand on redémarre la raspberry, on peut se connecter en bluetooth sans refaire la CLI mais on a l'impression que ça pose des problèmes
le mieux c'est que pour chaque enceinte bluetooth, on refasse le pair + trust + connect

4.
```bash
    # option 1
    pactl list cards
    # récupérer 'Name' et 'Active Profile'
    pactl load-module module-null-sink sink_name=delayed
    pactl load-module module-loopback latency_msec=2000 source=delayed.monitor sink=NAME.ACTIVE-PROFILE

    # option 2
    pactl info
    # récupérer 'Name' et 'Audio'
    pactl load-module module-null-sink sink_name=delayed
    pactl load-module module-loopback latency_msec=2000 source=delayed.monitor sink=NAME.AUDIO
```

Pour se connecter en VNC, `sudo raspi-config` puis *Interfacing Options > VNC > Activate VNC*
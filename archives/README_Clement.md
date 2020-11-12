# Configuration par Clément

## Synchronisation de deux enceintes bluetooth (simultaneous output) : une enceinte en filaire et une enceinte connectée en bluetooth

Utilisation de pulseaudio: installé par défaut (version 10.0)

### 1) Installation du desktop environnment (cf. à la fin)
Desktop environnement for the raspberry pi = XFCE
"lightweight desktop environment for UNIX-like operating systems. It aims to be fast and low on system resource" 


### 2) Branchement de la première enceinte bluetooth sur la sortie jack

### 3) Etablissement de la connection bluetooth avec la deuxième enceinte
```bash
    $ sudo bluetoothctl 
    $ agent on
    $ default-agent 
    $ scan on             
    # (addresses of all the Bluetooth devices around the Raspberry Pi will appear  XX:XX:XX:XX:XX:XX). 
    $ pair XX:XX:XX:XX:XX:XX
    $ connect XX:XX:XX:XX:XX:XX
    $ exit
```

Tips :
unpair a device : remove XX:XX:XX:XX:XX:XX  
disconnect a device : disconnect XX:XX:XX:XX:XX:XX  
trust a device (autoconnect next time) : trust XX:XX:XX:XX:XX:XX  

### 4) Installation de paprefs
paprefs - PulseAudio Preferences (paprefs) is a configuration dialog for the PulseAudio sound server.
```bash
    $ sudo apt-get install paprefs 
    $ paprefs
```
Attention, besoin d'un desktop environnment pour lancer la fenêtre graphique de configuration. 
Ensuite aller dans `Simultaneous output`. Et cliquer sur `Add virtual output device for simultaneous output on all local sound cards`.

Il faut redémarrer le service pulseaudio
```bash
    $ pulseaudio -k
    $ pulseaudio -D
```

### 5) Installation/mise à jour de pavucontrol: (3.0-3.1)
pavucontrol - A volume control for the PulseAudio sound server
```bash
    $ sudo apt-get install pavucontrol
```

### 6) Réglage manuel du délai (via interface graphique )
Aller dans `PulseAudio Volume Control`.
Dans l'onglet `Output Devices`, si tout fonctionne, on devrait voir une sortie appelée `Simultaneous output to [enceinte bluetooth et carte son de la raspberry]`.
Plus bas on peut voir les différents modules audio connectés et dans `advanced`, il est possible de modifier le délai (*latency offset*).


#### [+++++] Tips  
Jouer un mp3 avec vlc en ligne de commande
> nvlc <mp3_file>

Pour se connecter en rdp avec le desktop environnement xfce: 
https://makingstuffwork.net/technology/lightweight-desktop-raspberry-pi-with-xfce4/

Ne pas oubliez d'autoriser les connections avec xRDP:
>sudo nano /etc/X11/Xwrapper.config
Change the allowed_users=console to be allowed_users=anybody

Attention, j'ai pas réussi à me connecter en RDP avec le desktop environnement Pixel: peut-être qu'il y a un problème de compatibilité avec xrdp. J'ai pas essayé en modifiant les permissions dans Xwrapper.config ! 
#!/bin/bash

set -euo pipefail

if [[ `id -u` != 0 ]]; then
    echo >&2 "You must be root to run this script"
    exit 1
fi

log() {
    echo -e "\033[1;32m\u25CF BlueBox Installer: $@ \033[00m"
}

bashrc="#-----------------------------------------------------------
# BlueBox bashrc template
#-----------------------------------------------------------
alias ..='cd ..'
alias ...='cd ../..'

alias ls='ls --color=auto'
alias ll='ls -lh --colo=auto --group-directories-first'
alias lr='ls -lhR --colo=auto --group-directories-first'
alias la='ls -lhA --colo=auto --group-directories-first'
alias l='ls -CF --color=auto'

alias rm='rm -v'
alias cp='cp -v'
alias mv='mv -v'
alias ln='ln -v'

alias du='du -sh *'
alias lk='lsblk'
alias li='blkid'
alias grep='grep --color=auto'
alias egrep='egrep --color=auto'

alias st='git status'

export LS_COLORS='no=00:fi=00:rs=0:di=01;34:ln=01;36:mh=00:pi=40;33:so=01;35:do=01;35:bd=40;33;01:cd=40;33;01:or=40;31;01:su=37;41:sg=30;43:ca=30;41:tw=30;42:ow=34;42:st=37;44:ex=01;32:*.cmd=01;32:*.exe=01;32:*.com=01;32:*.btm=01;32:*.bat=01;32:*.sh=01;32:*.csh=01;32:*.out=01;32:*.class=01;32:*.c=00;31:*.cpp=00;31:*.java=00;33:*.py=00;33:*.html=00;36:*.css=00;32:*.php=00;35:*.js=00;35:*.tar=01;31:*.tgz=01;31:*.taz=01;31:*.tlz=01;31:*.txz=01;31:*.t7z=01;31:*.tbz=01;31:*.tbz2=01;31:*.tz=01;31:*.zip=01;31:*.z=01;31:*.Z=01;31:*.gz=01;31:*.xz=01;31:*.bz2=01;31:*.bz=01;31:*.rar=01;31:*.7z=01;31:*.rz=01;31:*.deb=01;31:*.rpm=01;31:*.jar=01;31:*.jpg=01;35:*.jpeg=01;35:*.gif=01;35:*.bmp=01;35:*.png=01;35:*.svg=01;35:*.svgz=01;35:*.mov=01;35:*.mpg=01;35:*.mpeg=01;35:*.m2v=01;35:*.mkv=01;35:*.webm=01;35:*.ogm=01;35:*.mp4=01;35:*.m4v=01;35:*.mp4v=01;35:*.vob=01;35:*.wmv=01;35:*.aac=00;36:*.au=00;36:*.flac=00;36:*.m4a=00;36:*.mid=00;36:*.midi=00;36:*.mka=00;36:*.mp3=00;36:*.mpc=00;36:*.ogg=00;36:*.wav=00;36:'
"
gitconfig="#-----------------------------------------------------------
# BlueBox gitconfig template
#-----------------------------------------------------------
[color]
    diff   = auto
    status = auto
    branch = auto
[alias]
    st   = status
    ad   = add
    aa   = add -A
    cm   = commit -S
    cmm  = commit -S -m
    cmam = commit -S -a -m
    df   = diff
    br   = branch
    co   = checkout
    lg   = log
    lp   = log -p
    ls   = log --stat
    ll   = log --color --graph --abbrev-commit --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr)%C(bold blue) <%an> %Creset'
    pl   = pull
    push = push -u --follow-tags
    ph   = push -u --follow-tags
[push]
    default = simple
[core]
    editor = vim
"
vimrc='"-----------------------------------------------------------
" BlueBox vimrc template
"-----------------------------------------------------------

" identation
set tabstop=4                               " 1 tab = 4 spaces
set shiftwidth=4                            " 1 indent = 4 spaces
set shiftround                              " use multiples of shiftwidth
set softtabstop=4
set expandtab                               " write spaces instead of tabs

" searching
set hlsearch
set incsearch
set ignorecase                              " searches are case-insensitive
set smartcase                               " unless we type an upper-case character

" when typing
set autoindent
set smartindent
set showmatch                               " show matching brace
set visualbell
set t_vb=
set t_u7=                                   " fix for Vim starting in Replace mode
noremap <F2> :set invpaste paste?<CR>
noremap <F3> :set invnumber number?<CR>
set showmode                                " if not already set

" interface look
set nu
noremap <F3> :set invnumber number?<CR>
"set laststatus=2
filetype indent plugin on
"set textwidth=80
set scrolloff=5
set sidescrolloff=5
syntax on
set t_Co=256
set background=dark                         " if not already set
colorscheme darkblue

" keyboard nice shortcuts
nnoremap ,, :w<CR>
nnoremap ;; :q<CR>
nnoremap ,; :x<CR>
nnoremap :: :%s///g<Left><Left>
'
inputrc="set bell-style none"



echo "BlueBox"
echo -e "This quick Installer will guide you through a few easy steps\n"


log "Appending to various configuration files (bashrc, gitconfig, vimrc, inputrc)"
    echo "$bashrc"    >> /home/pi/.bashrc
    echo "$gitconfig"  > /home/pi/.gitconfig
    echo "$vimrc"      > /home/pi/.vimrc
    echo "$vimrc"      > /root/.vimrc
    echo "$inputrc"    > /home/pi/.inputrc


log "Updating system packages (except chromium-browser and raspberrypi-kernel)"
    #apt-get remove -qq chromium-browser chromium-browser-l10n chromium-codecs-ffmpeg-extra
    #apt-mark hold raspberrypi-kernel raspberrypi-bootloader
    apt-get update
    #apt-get upgrade -qq
    apt-get autoremove -qq
    apt-get install -qq vim vlc


log "Removing bluealsa to avoid potential conflicts"
    apt-get remove -qq bluealsa


log "Installing and configuring PulseAudio to create a combined audio sink"
    # we alsol install ofono (this is not necessary, but it prevents from seeing this error in every log file)
    #   [pulseaudio] backend-ofono.c: Failed to register as a handsfree audio agent with ofono
    apt-get install -qq pulseaudio pulseaudio-module-bluetooth ofono
    pulseaudio_conf="

#!/usr/bin/pulseaudio -nF
#
# This file is part of PulseAudio.
#
# PulseAudio is free software; you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# PulseAudio is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with PulseAudio; if not, see <http://www.gnu.org/licenses/>.

# This startup script is used only if PulseAudio is started per-user
# (i.e. not in system mode)

.fail

### Automatically restore the volume of streams and devices
load-module module-device-restore
load-module module-stream-restore restore_device=false
load-module module-card-restore

### Automatically augment property information from .desktop files
### stored in /usr/share/application
load-module module-augment-properties

### Should be after module-*-restore but before module-*-detect
load-module module-switch-on-port-available

### Load audio drivers statically
### (it's probably better to not load these drivers manually, but instead
### use module-udev-detect -- see below -- for doing this automatically)
#load-module module-alsa-sink
#load-module module-alsa-source device=hw:1,0
#load-module module-oss device=\"/dev/dsp\" sink_name=output source_name=input
#load-module module-oss-mmap device=\"/dev/dsp\" sink_name=output source_name=input
#load-module module-null-sink
#load-module module-pipe-sink

### Automatically load driver modules depending on the hardware available
.ifexists module-udev-detect.so
load-module module-udev-detect tsched=0
.else
### Use the static hardware detection module (for systems that lack udev support)
load-module module-detect
.endif

### Automatically connect sink and source if JACK server is present
.ifexists module-jackdbus-detect.so
.nofail
load-module module-jackdbus-detect channels=2
.fail
.endif

### Automatically load driver modules for Bluetooth hardware
.ifexists module-bluetooth-policy.so
load-module module-bluetooth-policy
.endif

.ifexists module-bluetooth-discover.so
load-module module-bluetooth-discover autodetect_mtu=yes
.endif

### Load several protocols
.ifexists module-esound-protocol-unix.so
load-module module-esound-protocol-unix
.endif
load-module module-native-protocol-unix

### Network access (may be configured with paprefs, so leave this commented
### here if you plan to use paprefs)
#load-module module-esound-protocol-tcp
#load-module module-native-protocol-tcp
#load-module module-zeroconf-publish

### Load the RTP receiver module (also configured via paprefs, see above)
#load-module module-rtp-recv

### Load the RTP sender module (also configured via paprefs, see above)
#load-module module-null-sink sink_name=rtp format=s16be channels=2 rate=44100 sink_properties=\"device.description='RTP Multicast Sink'\"
#load-module module-rtp-send source=rtp.monitor

### Load additional modules from GSettings. This can be configured with the paprefs tool.
### Please keep in mind that the modules configured by paprefs might conflict with manually
### loaded modules.
.ifexists module-gsettings.so
.nofail
load-module module-gsettings
.fail
.endif


### Automatically restore the default sink/source when changed by the user
### during runtime
### NOTE: This should be loaded as early as possible so that subsequent modules
### that look up the default sink/source get the right value
load-module module-default-device-restore

### Automatically move streams to the default sink if the sink they are
### connected to dies, similar for sources
load-module module-rescue-streams

### Make sure we always have a sink around, even if it is a null sink.
load-module module-always-sink

### Honour intended role device property
load-module module-intended-roles

### Automatically suspend sinks/sources that become idle for too long
load-module module-suspend-on-idle

### If autoexit on idle is enabled we want to make sure we only quit
### when no local session needs us anymore.
.ifexists module-console-kit.so
load-module module-console-kit
.endif
.ifexists module-systemd-login.so
load-module module-systemd-login
.endif

### Enable positioned event sounds
load-module module-position-event-sounds

### Cork music/video streams when a phone stream is active
load-module module-role-cork

### Modules to allow autoloading of filters (such as echo cancellation)
### on demand. module-filter-heuristics tries to determine what filters
### make sense, and module-filter-apply does the heavy-lifting of
### loading modules and rerouting streams.
load-module module-filter-heuristics
load-module module-filter-apply

### Make some devices default
#set-default-sink output
#set-default-source input

load-module module-combine-sink sink_name=bluebox_combined
set-default-sink bluebox_combined
    "
    echo "$pulseaudio_conf" > /etc/pulse/default.pa
    sudo -u pi pulseaudio --start


log "Adding pi and root to pulseaudio user groups (this is not necessary but will be if we want to turn pulseaudio into a service)"
    adduser pi audio
    adduser root audio
    adduser pulse audio
    adduser pi pulse-access
    adduser root pulse-access


log "Pasting asoundrc configuration"
    asoundrc="pcm.pulse {
        type pulse
    }
         
    ctl.pulse {
        type pulse
    }
         
    pcm.default pulse
    ctl.default pulse
    "
    echo "$asoundrc" > /etc/asound.conf
    echo "$asoundrc" > /home/pi/.asoundrc


log "Installing and configuring Supervisor"
    apt-get install -qq supervisor
    supervisord_conf="
; supervisor config file

[unix_http_server]
file=/var/run/supervisor.sock   ; (the path to the socket file)
chmod=0700                       ; sockef file mode (default 0700)

[supervisord]
logfile=/var/log/supervisor/supervisord.log ; (main log file;default \$CWD/supervisord.log)
pidfile=/var/run/supervisord.pid ; (supervisord pidfile;default supervisord.pid)
childlogdir=/var/log/supervisor            ; ('AUTO' child log dir, default \$TEMP)

; the below section must remain in the config file for RPC
; (supervisorctl/web interface) to work, additional interfaces may be
; added by defining them in separate rpcinterface: sections
[rpcinterface:supervisor]
supervisor.rpcinterface_factory = supervisor.rpcinterface:make_main_rpcinterface

[supervisorctl]
serverurl=unix:///var/run/supervisor.sock ; use a unix:// URL  for a unix socket

; The [include] section can just contain the files setting.  This
; setting can list multiple files (separated by whitespace or
; newlines).  It can also contain wildcards.  The filenames are
; interpreted as relative to this file.  Included files *cannot*
; include files themselves.

[include]
files = /etc/supervisor/conf.d/*.conf

[program:launch_bluebox_server]
command = /home/pi/bluebox/run.sh
autostart = true
autorestart = true

[program:create_bluetooth_sink]
command = /bin/hciconfig hci0 class 0x200420

[program:kill_piwiz]
command = /usr/bin/sudo /usr/bin/pkill piwiz
"
    echo "$supervisord_conf" > /etc/supervisor/supervisord.conf


log "Installing Python dependencies for the BlueBox server"
    apt-get install -qq python3-pip
    apt-get install -qq libcairo2-dev
    pip3 install --quiet flask Flask-JSON python-dotenv
    echo 'export PATH="/home/pi/.local/bin:$PATH"' >> /home/pi/.bashrc


log "Installing Python dependencies for Bluetool"
    apt-get install -qq libcairo2-dev


log "Installation success."

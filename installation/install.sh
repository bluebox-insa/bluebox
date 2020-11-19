#!/bin/bash

set -e
#set -ue -o pipefail

echo -e "\033[1;35m>>> Paste various configurations (bashrc, gitconfig, vimrc, ...) and install vim \033[00m"
    bashrc="#-----------------------------------------------------------
    # INNOTECH-MVP bashrc template
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
    # INNOTECH-MVP gitconfig template
    #-----------------------------------------------------------
    [user]
        name = Gabriel Forien
        email = gforien+dev@gmail.com
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

    inputrc="set bell-style none
    "

    vimrc='"-----------------------------------------------------------
    " INNOTECH-MVP vimrc template
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
    echo "$bashrc" >> $HOME/.bashrc
    echo "$bashrc" >> $HOME/.bashrc
    echo "$gitconfig" > $HOME/.gitconfig
    echo "$vimrc" > $HOME/.vimrc
    echo "$inputrc" > $HOME/.inputrc
    sudo apt-get install -y vim
    # read -p $'\e[1;35m[Press Enter to continue]\e[0m'


echo -e "\033[1;35m>>> Make sure everything is up to date \033[00m"
    sudo apt-get update
    sudo apt-get upgrade -y
    sudo apt-get autoremove -y
    # read -p $'\e[1;35m[Press Enter to continue]\e[0m'

echo -e "\033[1;35m>>> Make sure that bluealsa is not installed to avoid potential conflicts \033[00m"
    sudo apt-get remove -y bluealsa
    # read -p $'\e[1;35m[Press Enter to continue]\e[0m'

echo -e "\033[1;35m>>> Install and launch pulseaudio \033[00m"
    sudo apt-get install -y pulseaudio pulseaudio-module-bluetooth
    pulseaudio --start
    # read -p $'\e[1;35m[Press Enter to continue]\e[0m'


echo -e "\033[1;35m>>> Add users to user groups (This is not necessary but will be if we want to turn pulseaudio into a service) \033[00m"
    sudo adduser pi audio
    sudo adduser root audio
    sudo adduser pulse audio
    sudo adduser pi pulse-access
    sudo adduser root pulse-access
    # read -p $'\e[1;35m[Press Enter to continue]\e[0m'

echo -e "\033[1;35m>>> Paste asoundrc configuration \033[00m"
    asoundrc="pcm.pulse {
        type pulse
    }
         
    ctl.pulse {
        type pulse
    }
         
    pcm.default pulse
    ctl.default pulse
    "
    sudo echo "$asoundrc" > /etc/asound.conf
    sudo echo "$asoundrc" > ~/.asoundrc
    # read -p $'\e[1;35m[Press Enter to continue]\e[0m'

echo -e "\033[1;35m>>> Check that selected mode is a2dp_sink \033[00m"
    pactl list
    # read -p $'\e[1;35m[Press Enter to continue]\e[0m'

echo -e "\033[1;35m>>> Create simultaneous audio output \033[00m"
    pactl load-module module-combine-sink
    # read -p $'\e[1;35m[Press Enter to continue]\e[0m'

echo -e "\033[1;35m>>> Download an audio sample \033[00m"
    wget "https://file-examples-com.github.io/uploads/2017/11/file_example_MP3_1MG.mp3"
    # read -p $'\e[1;35m[Press Enter to continue]\e[0m'

echo -e "\033[1;35m>>> Install Python dependencies \033[00m"
    sudo apt-get install -y python3-pip
    sudo apt-get install -y libcairo2-dev
    pip3 install flask Flask-JSON python-dotenv
    echo 'export PATH="/$HOME/.local/bin:$PATH"' >> ~/.bashrc

echo -e "\033[1;35m>>> Install cairo \033[00m"
    sudo apt-get install -y libcairo2-dev
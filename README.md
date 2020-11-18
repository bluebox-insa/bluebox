# Innotech MVP :headphones::zap:

Turn your **Raspberry Pi** into a **Bluetooth hub** to play your music through multiple bluetooth **synced** speakers 🔊🔊🔊.

1. [Requirements 📜](<#Requirements 📜>)
1. [Your path to multi-devices sound on Linux ! 🔥](./installation/README.md)
1. [Setup Python server 🐍](<#Setup Python server 🐍>)

## Requirements 📜
- Raspberry pi (model 3B used)
- Jack cable
- 2 speakers :
    - 1 in bluetooth mode
    - 1 in AUX mode (connected with JACK cable to the headphone output of the Raspberry)
    ![architecture](./installation/architecture.png)

## Setup Python server 🐍
```bash
    pip3 install flask Flask-JSON python-dotenv
    # [git clone innotech-insa/bluetool and follow installation steps]
    flask run --host 192.168.0.142
```

[Source - Flask JSON](https://pypi.org/project/Flask-JSON/)

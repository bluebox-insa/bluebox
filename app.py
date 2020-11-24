from flask import Flask
from flask_json import FlaskJSON, JsonError, json_response, as_json
from bluetool.bluetool import Bluetooth

app = Flask(__name__)
FlaskJSON(app)
bluetooth = Bluetooth()

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/devices/scan')
@as_json
def get_devices():
    bluetooth.scan()
    devices = bluetooth.get_available_devices()
    return devices


@app.route('/devices/paired')
@as_json
def get_devices_paired():
    devices = bluetooth.get_paired_devices()
    return devices


@app.route('/devices/connected')
@as_json
def get_devices_connected():
    devices = bluetooth.get_connected_devices()
    return devices


@app.route('/pair/<mac_addr>', methods=["GET", "PUT"])
@as_json
def get_pair(mac_addr):
    return f"Trying to pair with {mac_addr}   =>   {bluetooth.pair(mac_addr)}"


@app.route('/trust/<mac_addr>', methods=["GET", "PUT"])
@as_json
def get_trust(mac_addr):
    return f"Trying to trust with {mac_addr}   =>   {bluetooth.trust(mac_addr)}"


@app.route('/connect/<mac_addr>', methods=["GET", "PUT"])
@as_json
def get_connect(mac_addr):
    inArrayC = False
    for i in bluetooth.get_connected_devices():
        print("value: " + str(i.values()))
        if mac_addr.encode() in i.values():
            inArrayC = True
    inArrayPaired = False
    for i in bluetooth.get_paired_devices():
        print("value: " + str(i.values()))
        if mac_addr.encode() in i.values():
            inArrayPaired = True
    if inArrayC:
        return ("already connected", 200)
    elif inArrayPaired:
        isConnected = bluetooth.connect(mac_addr)
        return ("connect.... ok", 200 if isConnected else 500)
    else:
        isPaired = bluetooth.pair(mac_addr)
        if isPaired:
            isConnected = bluetooth.connect(mac_addr)
            return ("pair.... ok<br>connect.... ok", 200 if isConnected else 500)
        else:
            return ("pair.... failed", 500)

@app.route('/disconnect/<mac_addr>', methods=["GET", "PUT"])
@as_json
def get_disconnect(mac_addr):
    inArray = False
    for i in bluetooth.get_connected_devices():
        print("value: " + str(i.values()))
        if mac_addr.encode() in i.values():
            inArray = True
    if inArray:
        isDisconnected = bluetooth.disconnect(mac_addr)
        return ("Disconnect .... ok", 200 if isDisconnected else 500)
    else:
        return ("Device is already disconnected .... failed", 200)


@app.route('/play', methods=["GET", "PUT"])
@as_json
def get_play():
    from subprocess import Popen
    try:
        command="/usr/bin/cvlc -A pulse --intf http --http-host "+argv[1] +" --http-password cookie /home/pi/music.mp3"
        Popen(command.split(" "), stdout=None)
        return True
    except Exception as e:
        print(f"Exception at {current_func()}: {e}")
    return False


@app.route('/controllers', methods=["GET", "PUT"])
@as_json
def get_controllers():
    if request.method == "GET":
        controllers = []
        try:
            pass
        except Exception as e:
            print(f"Exception at {current_func()}: {e}")
        return controllers

    elif request.method == "PUT":
        pass

if __name__ == '__main__':
    from sys import argv
    app.run(host=argv[1]) if argv[1] else app.run(host="192.168.0.142")
    # debug = True
    # host = ""
    # port = ""

    

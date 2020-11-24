from flask import Flask,request
from flask_json import FlaskJSON, JsonError, json_response, as_json
from bluetool.bluetool import Bluetooth
import subprocess

app = Flask(__name__)
FlaskJSON(app)
bluetooth = Bluetooth()
adapters  = bluetooth.list_interfaces()
nb_bt_controller=2
controller_list=getBtControllerMacAddr()

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
    nb_connectedDevices=len(bluetooth.get_connected_devices())
    print("number of connnected device = ",nb_connectedDevices)
    if nb_connectedDevices==0:
        connectBluetoothDevice(mac_addr,interface_nb=1)
        return ("connect.... ok",200)
    elif nb_connectedDevices == 1:
        connectBluetoothDevice(mac_addr,interface_nb=0)
        return ("connect.... ok",200)
    else:
        return ("too many bluetooth devices.... failed", 500)
    

''' def get_connect(mac_addr):
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
            return ("pair.... failed", 500) '''

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
        hostIpAddress=request.host.split(':')[0]
        command="/usr/bin/cvlc -A pulse --intf http --http-host "+ hostIpAddress +" --http-password cookie /home/pi/music.mp3"
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




def getBtControllerMacAddr():
    command='hcitool dev | grep -o \"[[:xdigit:]:]\{11,17\}\"'
    mac_controller_addr=subprocess.check_output(command, shell=True)
    controller_list=mac_controller_addr.split('\n')[0:nb_bt_controller]
    print("my controller list is : "+controller_list )
    return controller_list

def connectBluetoothDevice(mac_addr,interface_nb):
    process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    process.stdin.write('select '+controller_list[interface_nb]+'\n')
    process.stdin.flush()
    process.stdin.write('pair '+ mac_addr+'\n')
    process.stdin.flush()
    process.stdin.write('connect '+ mac_addr+'\n')
    process.stdin.flush()
    process.stdin.write('exit\n')
    process.stdin.flush()
    output, errors = process.communicate()
    #print(output.decode())


def isDeviceAlreadyConnected(mac_addr):
    for i in bluetooth.get_connected_devices():
        print("value: " + str(i.values()))
        if mac_addr.encode() in i.values():
            return True
    return False

def isDeviceAlreadyPaired(mac_addr):
    for i in bluetooth.get_paired_devices():
        print("value: " + str(i.values()))
        if mac_addr.encode() in i.values():
            return True
    return False

if __name__ == '__main__':
    from sys import argv
    app.run(host=argv[1]) if argv[1] else app.run(host="192.168.0.142")
    # debug = True
    # host = ""
    # port = ""

    

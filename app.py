import subprocess
import time
import logging
from flask import Flask,request
from flask_json import FlaskJSON, JsonError, json_response, as_json
from bluetool.bluetool import Bluetooth


logging.basicConfig(level = logging.DEBUG)
logger                    = logging.getLogger(__name__)
app                       = Flask(__name__)
FlaskJSON(app)
bluetooth                 = Bluetooth()
controllers               = get_controllers()
currentControllerIndex    = 1

def get_controllers():
    command         = 'hcitool dev | grep -o \"[[:xdigit:]:]\{11,17\}\"'
    controllers_str = subprocess.check_output(command, shell=True).decode()
    controllers     = controllers_str.split('\n')
    return controllers


################################
#         ROUTES
################################
@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/scan')
@as_json
def scan_for_bluetooth_devices():
    bluetooth.scan() 
    devices = bluetooth.get_available_devices()
    return devices

@app.route('/devices')
@as_json
def get_connected_bluetooth_devices():
    devices = bluetooth.get_connected_devices()
    return devices


@app.route('/connect/<mac_addr>')
@as_json
def connect_bluetooth_device(mac_addr):
    process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    logger.debug(f"select {controllers[currentControllerIndex]}\n")
    process.stdin.write(f"select {controllers[currentControllerIndex]}\n")
    process.stdin.flush()
    time.sleep(2)
    process.stdin.write("scan on\n")
    process.stdin.flush()
    time.sleep(5)
    process.stdin.write("scan off\n")
    process.stdin.flush()
    time.sleep(1)
    logger.debug(f"pair {mac_addr}\n")
    process.stdin.write(f"pair {mac_addr}\n")
    process.stdin.flush()
    time.sleep(1)
    logger.debug(f"connect {mac_addr}\n")
    process.stdin.write(f"connect {mac_addr}\n")
    process.stdin.flush()
    time.sleep(4)
    process.stdin.write('exit\n')
    process.stdin.flush()
    time.sleep(1)
    output, errors = process.communicate()
    print(output,errors)


@app.route('/play')
@as_json
def get_play():
    try:
        hostIpAddress = request.host.split(':')[0]
        command = f"/usr/bin/cvlc -A pulse --intf http --http-host {hostIpAddress} --http-password cookie /home/pi/music.mp3"
        subprocess.Popen(command.split(" "), stdout=None)
        return "OK", 200
    except Exception as e:
        logger.error(f"Exception at {current_func()}: {e}")
        return f"Exception at {current_func()}: {e}", 500


#il faudrait pouvoir activer le scan sur la deuxieme interface aussi sinon pas possible de connecter la deuxieme enceinte
def activateScanForAllBtController():
    process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,text=True)
    for i in range(nb_bt_controller):
        process.stdin.write('select '+controller_list[i]+'\n')
        time.sleep(1)
        process.stdin.write('scan on\n')
        time.sleep(1)
        process.stdin.write('exit\n')


if __name__ == '__main__':
    from sys import argv
    app.run(host=argv[1]) if argv[1] else app.run(host="192.168.0.137")

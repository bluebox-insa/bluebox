#!/usr/bin/python3
import subprocess
import time
import logging
from flask import Flask,request
from flask_json import FlaskJSON, JsonError, json_response, as_json
from bluetool.bluetool import Bluetooth


def get_controllers():
    command         = 'hcitool dev | grep -o \"[[:xdigit:]:]\{11,17\}\"'
    controllers_str = subprocess.check_output(command, shell=True).decode()
    controllers     = controllers_str.split('\n')
    return controllers

logging.basicConfig(level = logging.DEBUG)
logger                    = logging.getLogger(__name__)
app                       = Flask(__name__)
FlaskJSON(app)
bluetooth                 = Bluetooth()
controllers               = get_controllers()
currentControllerIndex    = 1


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

@app.route('/connect_input/<mac_addr>')
@as_json
def connect_smartphone(mac_addr):
    if isMacAddrInDevices(mac_addr, bluetooth.get_connected_devices()):
        return "device already connected", 200

    global controllerIndex, devicesRecord
    process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    logger.debug(f"select controllers[0] = {controllers[0]}\n")
    process.stdin.write(f"select {controllers[0]}\n")
    process.stdin.flush()

    if 0 in devicesRecord.keys():
        logger.debug(f"controllers[{controllerIndex}] is already connected to {devicesRecord[controllerIndex]}")
        logger.debug(f"disconnect {devicesRecord[controllerIndex]}")
        process.stdin.write(f"disconnect {devicesRecord[controllerIndex]}")
        process.stdin.flush()
        time.sleep(5)

    if not isMacAddrInDevices(mac_addr, bluetooth.get_paired_devices()):
        process.stdin.write("scan on\n")
        process.stdin.flush()
        time.sleep(2)

        logger.debug(f"pair {mac_addr}\n")
        process.stdin.write(f"pair {mac_addr}\n")
        process.stdin.flush()
        time.sleep(7)
        process.stdin.write(f"yes\n")
        process.stdin.flush()
        time.sleep(3)
    else:
        logger.debug(f"scan on\n")
        process.stdin.write(f"scan on\n")
        process.stdin.flush()
        time.sleep(4)

    logger.debug(f"connect {mac_addr}\n")
    process.stdin.write(f"connect {mac_addr}\n")
    process.stdin.flush()
    time.sleep(4)

    out, err = process.communicate()
    print(out)

    if isMacAddrInDevices(mac_addr, bluetooth.get_connected_devices()):
        devicesRecord[controllerIndex] = mac_addr
        return "ok", 200
    else:
        return "erreur", 500


@app.route('/connect/<mac_addr>')
@as_json
def connect_bluetooth_device(mac_addr):
    process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    logger.debug(f"select {controllers[currentControllerIndex]}\n")
    process.stdin.write(f"select {controllers[currentControllerIndex]}\n")
    process.stdin.flush()

    logger.debug(f"is {controllerIndex} in {devicesRecord.keys()} : {controllerIndex in devicesRecord.keys()}")
    if controllerIndex in devicesRecord.keys():
        logger.debug(f"controllers[{controllerIndex}] is already connected to {devicesRecord[controllerIndex]}")
        logger.debug(f"disconnect {devicesRecord[controllerIndex]}")
        process.stdin.write(f"disconnect {devicesRecord[controllerIndex]}")
        process.stdin.flush()
        time.sleep(5)

    process.stdin.write("scan on\n")
    process.stdin.flush()
    time.sleep(3)

    if not isMacAddrInDevices(mac_addr, bluetooth.get_paired_devices()):
        logger.debug(f"pair {mac_addr}\n")
        process.stdin.write(f"pair {mac_addr}\n")
        process.stdin.flush()
        time.sleep(6)

    logger.debug(f"connect {mac_addr}\n")
    process.stdin.write(f"connect {mac_addr}\n")
    process.stdin.flush()
    time.sleep(4)

    if isMacAddrInDevices(mac_addr, bluetooth.get_connected_devices()):
        devicesRecord[controllerIndex] = mac_addr
        controllerIndex += 1
        logger.debug(f"controllerIndex set to {controllerIndex}")
        return "ok", 200
    else:
        return "erreur", 500

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


# launch as ./app.py
if __name__ == '__main__':
    from sys import argv
    app.run(host=argv[1]) if len(argv)>1 else app.run(host="10.3.141.1")

# or launch with
# flask run --host "$(hostname -I | cut -d ' ' -f 1)"

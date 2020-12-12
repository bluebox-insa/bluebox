#!/usr/bin/python3

import subprocess
import time
import logging
from flask import Flask,request
from flask_json import FlaskJSON, JsonError, json_response, as_json
from bluetool.bluetool import Bluetooth

# global vars
logging.basicConfig(level = logging.DEBUG)
logger                    = logging.getLogger(__name__)
app                       = Flask(__name__)
FlaskJSON(app)
bluetooth                 = Bluetooth()
controllers               = subprocess.check_output('hcitool dev | grep -o \"[[:xdigit:]:]\{11,17\}\"', shell=True).decode().split('\n')[:-1]
controllers.reverse()
currentControllerIndex    = 1
devicesRecord             = {}

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

@app.route('/connect_in/<mac_addr>')
def connect_input_device(mac_addr):
    global controller, controllerIndex, devicesRecord

    if isMacAddrInDevices(mac_addr, bluetooth.get_connected_devices()):
        return "device already connected", 200

    process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

    logger.debug(f"select controllers[0] = {controllers[0]}\n")
    process.stdin.write(f"select {controllers[0]}\n")
    process.stdin.flush()

    # disconnect device if it is already connected
    if 0 in devicesRecord.keys():
        logger.debug(f"controllers[0] is already connected to {devicesRecord[0]}")
        logger.debug(f"disconnect {devicesRecord[0]}")
        process.stdin.write(f"disconnect {devicesRecord[0]}")
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


@app.route('/connect_out/<mac_addr>')
def connect_output_device(mac_addr):
    global controller, controllerIndex, devicesRecord

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

    subprocess.Popen(f"/usr/bin/cvlc -A pulse --intf http --http-host {hostIpAddress} --http-password cookie /home/pi/music.mp3".split(" "), stdout=None)
    
    if isMacAddrInDevices(mac_addr, bluetooth.get_connected_devices()):
        devicesRecord[controllerIndex] = mac_addr
        controllerIndex += 1
        logger.debug(f"controllerIndex set to {controllerIndex}")
        return "ok", 200
    else:
        return "erreur", 500

@app.route('/reset_in')
def reset_input_device():
    global controller, controllerIndex, devicesRecord

    process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    ret = ""

    ret += f"select {controllers[0]}\n"
    process.stdin.write(f"select {controllers[0]}\n")
    process.stdin.flush()

    if request.args.get('hard'):
        ret += f"disconnect {devicesRecord[0]}\n"
        process.stdin.write(f"disconnect {devicesRecord[0]}\n")
    else:
        ret += f"remove {devicesRecord[0]}\n"
        process.stdin.write(f"remove {devicesRecord[0]}\n")

    process.stdin.flush()
    time.sleep(1)

    out, err = process.communicate()
    print(out)

    if devicesRecord[0] not in bluetooth.get_connected_devices():
        return ret, 200
    else:
        return "erreur", 500


@app.route('/reset_out')
def reset_output_device():
    global controller, controllerIndex, devicesRecord

    process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    ret = ""

    input_device = deviceRecord[0]
    for c in controllers[1:].keys():
        ret += f"select {controllers[0]}\n"
        process.stdin.write(f"select {controllers[0]}\n")
        process.stdin.flush()

        for d in bluetooth.get_connected_devices():
            if d != input_device:
                #if request.args.get('hard'):
                ret += f"disconnect {d}\n"
                process.stdin.write(f"disconnect {d}\n")
                #else:
                #    ret += f"remove {devicesRecord[0]}\n"
                #    process.stdin.write(f"remove {devicesRecord[0]}\n")

    process.stdin.flush()
    time.sleep(1)

    out, err = process.communicate()
    print(out)

    if len(bluetooth.get_connected_devices()) == 0:
        return "ok", 200
    else:
        return "erreur", 500

# launch as ./app.py
if __name__ == '__main__':
    from sys import argv
    app.run(host=argv[1]) if len(argv)>1 else app.run(host="192.168.0.142")

# or launch with
# flask run --host "$(hostname -I | cut -d ' ' -f 1)"

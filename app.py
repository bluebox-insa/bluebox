#!/usr/bin/python3

import subprocess
import time
import logging
from flask import Flask,request
from flask_json import FlaskJSON, JsonError, json_response, as_json
logging.getLogger("bluetool").setLevel(logging.WARNING)
# logging.getLogger("werkzeug").setLevel(logging.ERROR)
from bluetool.bluetool import Bluetooth

# global vars
logging.basicConfig(level = logging.INFO)
logger                    = logging.getLogger(__name__)
app                       = Flask(__name__)
FlaskJSON(app)
bluetooth                 = Bluetooth()
controllers               = subprocess.check_output('hcitool dev | grep -o \"[[:xdigit:]:]\{11,17\}\"', shell=True).decode().split('\n')[:-1]
controllers.reverse()

controllerIndex    = 1
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

    logger.info(f"select controllers[0] = {controllers[0]}\n")
    process.stdin.write(f"select {controllers[0]}\n")
    process.stdin.flush()

    # disconnect device if it is already connected
    if 0 in devicesRecord.keys():
        logger.info(f"controllers[0] is already connected to {devicesRecord[0]}")
        logger.info(f"disconnect {devicesRecord[0]}")
        process.stdin.write(f"disconnect {devicesRecord[0]}")
        process.stdin.flush()
        time.sleep(5)

    if not isMacAddrInDevices(mac_addr, bluetooth.get_paired_devices()):
        process.stdin.write("scan on\n")
        process.stdin.flush()
        time.sleep(2)

        logger.info(f"pair {mac_addr}\n")
        process.stdin.write(f"pair {mac_addr}\n")
        process.stdin.flush()
        time.sleep(7)
        process.stdin.write(f"yes\n")
        process.stdin.flush()
        time.sleep(3)
    else:
        logger.info(f"scan on\n")
        process.stdin.write(f"scan on\n")
        process.stdin.flush()
        time.sleep(4)

    logger.info(f"connect {mac_addr}\n")
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

    logger.info(f"select {controllers[controllerIndex]}\n")
    process.stdin.write(f"select {controllers[controllerIndex]}\n")
    process.stdin.flush()

    logger.info(f"is {controllerIndex} in {devicesRecord.keys()} : {controllerIndex in devicesRecord.keys()}")
    if controllerIndex in devicesRecord.keys():
        logger.info(f"controllers[{controllerIndex}] is already connected to {devicesRecord[controllerIndex]}")
        logger.info(f"disconnect {devicesRecord[controllerIndex]}")
        process.stdin.write(f"disconnect {devicesRecord[controllerIndex]}")
        process.stdin.flush()
        time.sleep(5)

    process.stdin.write("scan on\n")
    process.stdin.flush()
    time.sleep(3)

    if not isMacAddrInDevices(mac_addr, bluetooth.get_paired_devices()):
        logger.info(f"pair {mac_addr}\n")
        process.stdin.write(f"pair {mac_addr}\n")
        process.stdin.flush()
        time.sleep(6)

    logger.info(f"connect {mac_addr}\n")
    process.stdin.write(f"connect {mac_addr}\n")
    process.stdin.flush()
    time.sleep(4)

    if isMacAddrInDevices(mac_addr, bluetooth.get_connected_devices()):
        devicesRecord[controllerIndex] = mac_addr
        controllerIndex += 1
        logger.info(f"controllerIndex set to {controllerIndex}")
        beep()
        return "ok", 200
    else:
        return "erreur", 500

@app.route('/reset_in')
def reset_input_device():
    global controller, controllerIndex, devicesRecord

    # input device is already disconnected
    if 0 not in devicesRecord.keys():
        return "ok", 200

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
        devicesRecord.pop(0)
        return ret, 200
    else:
        return "erreur", 500


@app.route('/reset_out')
def reset_output_device():
    global controller, controllerIndex, devicesRecord


    process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    ret = ""

    input_device = devicesRecord[0]
    for c in controllers[1:]:
        logger.debug(f"select {c}")
        ret += f"select {c}\n"
        process.stdin.write(f"select {c}\n")
        process.stdin.flush()

        for d in bluetooth.get_connected_devices():
            d = d["mac_address"].decode()
            if d != input_device:
                #if request.args.get('hard'):
                logger.debug(f"disconnect {d}")
                ret += f"disconnect {d}\n"
                process.stdin.write(f"disconnect {d}\n")
                process.stdin.flush()
                time.sleep(1)
                #else:
                #    ret += f"remove {devicesRecord[0]}\n"
                #    process.stdin.write(f"remove {devicesRecord[0]}\n")


    out, err = process.communicate()
    print(out)

    still_connected = bluetooth.get_connected_devices()
    if len(still_connected) == 1 and isMacAddrInDevices(input_device, still_connected):
        return "ok", 200
    else:
        return "erreur", 500

def isMacAddrInDevices(mac_addr, devices):
    for d in devices:
        if mac_addr.encode() in d.values():
            return True
    return False

def beep():
    subprocess.Popen(f"(cvlc /home/pi/bluebox/beep_6sec.wav &) >/dev/null 2>&1", shell=True)


# launch as ./app.py
if __name__ == '__main__':
    from sys import argv
    app.run(host=argv[1]) if len(argv)>1 else app.run(host="192.168.0.142")

# or launch with
# flask run --host "$(hostname -I | cut -d ' ' -f 1)"

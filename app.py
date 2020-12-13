#!/usr/bin/python3
"""Bluebox server

This server is meant to be ran on a Raspberry Pi with multiple bluetooth controllers.
It must be combined with a special PulseAudio configuration (see /installation/install.sh script) in order to work properly.
Controller 0 (/dev/hci0) will be receiving an audio stream.
Controllers 1, 2, 3.. (/dev/hci1, /dev/hci2, /dev/hci3...) will be forwarding this audio stream to bluetooth speakers.

Usage:
    1) User retrieves a list of available devices
        GET /scan -> HTTP 200 (OK) with the following body
            [
                {'name': 'Redmi',       'mac_address': '20:34:FB:A5:11:E8'}
                {'name': 'UE BOOM 2',   'mac_address': '88:C6:26:EE:BC:FE'}
                {'name': 'BLP9820',     'mac_address': '30:21:15:54:78:AA'}
                {'name': '<unknown>',   'mac_address': '00:1A:7D:DA:71:13'}
                {'name': '<unknown>',   'mac_address': '67:A8:88:C6:26:C3'}
            ]

    2) User requests for the Raspberry Pi to connect to several output devices (e.g. Bluetooth speakers)
       GET /connect_out/88:C6:26:EE:BC:FE -> HTTP 200 (OK)
       GET /connect_out/30:21:15:54:78:AA -> HTTP 200 (OK)
       GET /connect_out/00:1A:7D:DA:71:13 -> HTTP 200 (OK)

    3) User requests for the Raspberry Pi to connect to an input device (e.g. a smartphone)
       GET /connect_in/20:34:FB:A5:11:E8 -> HTTP 200 (OK)

    4) Done. Any audio stream will now automatically follow this path
        - emission from the input device on interface 20:34:FB:A5:11:E8
        - reception by the Raspberry Pi on interface /dev/hci0
        - simultaneous forwarding to interfaces /dev/hci1, /dev/hci2, /dev/hci3 and emission again
        - reception on the output devices on interfaces 88:C6:26:EE:BC:FE, 30:21:15:54:78:AA, 00:1A:7D:DA:71:13

       Once this configuration has been established, the audio streams rely solely on the Bluetooth controllers and PulseAudio.
"""



#---------------------------
#          imports
#---------------------------
import subprocess, logging
logging.getLogger("bluetool").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING)
from time import sleep

from flask import Flask, request
from flask_json import FlaskJSON, as_json

# this is the package bluebox/bluetool forked from emlid/bluetool and adapted for multi-controller support
from bluetool.bluetool import Bluetooth




#-----------------------------------
#          global variables
#-----------------------------------
logging.basicConfig(level = logging.INFO)
logger                    = logging.getLogger(__name__)

app                       = Flask(__name__)
FlaskJSON(app)

# bluetool handler, used only to scan nearby bluetooth devices or retrieve currently connected bluetooth devices
bluetooth                 = Bluetooth()

# list of MAC addresses of the bluetooth controllers on the Raspberry Pi
# controllers[0] = /dev/hci0,   controllers[1] = /dev/hci1 and so on
controllers               = subprocess.check_output('hcitool dev | grep -o \"[[:xdigit:]:]\{11,17\}\"', shell=True).decode().split('\n')[:-1]
controllers.reverse()
controller_idx            = 1

# dictionnary of connected devices
devices                   = {}


#---------------------------
#          routes
#---------------------------
@app.route('/')
def status():
    return "OK", 200


@app.route('/scan')
@as_json
def scan_for_bluetooth_devices():
    """ scan_for_bluetooth_devices

    Performs a scan of nearby bluetooth devices by calling the bluetool library (i.e. bluez).
    Devices must be in DISCOVERABLE state to be detected.
    The scan is performed with any of the bluetooth controllers and takes ~3 seconds.
    The scan cannot distinguish output devices (e.g. Bluetooth speakers) from input devices (e.g. smartphones).
    During our tests, the scan also detected LE Bluetooth devices.
    Sometimes a device name cannot be retrieved, so it is marked <unknown>.

    Args: <none>

    Returns:
        a JSON array of the devices found, for instance
        [
            {'name': 'Redmi',       'mac_address': '20:34:FB:A5:11:E8'}
            {'name': 'UE BOOM 2',   'mac_address': '88:C6:26:EE:BC:FE'}
            {'name': 'BLP9820',     'mac_address': '30:21:15:54:78:AA'}
            {'name': '<unknown>',   'mac_address': '00:1A:7D:DA:71:13'}
            {'name': '<unknown>',   'mac_address': '67:A8:88:C6:26:C3'}
        ]

    Raises: <none>
    """
    bluetooth.scan()
    found_devices = bluetooth.get_available_devices()
    return found_devices

@app.route('/devices')
@as_json
def get_connected_bluetooth_devices():
    """ get_connected_bluetooth_devices

    Any device connected to any of the bluetooth controllers is retrieved.
    But there is no way to know which device is connected to which controller. (That's why we have a gloabl {device} dictionnary).
    Connected devices are usually not marked as <unknown> as is scan_for_bluetooth_devices().

    Args: <none>

    Returns:
        a JSON array of the devices connected, for instance
        [
            {'name': 'Redmi',       'mac_address': '20:34:FB:A5:11:E8'}
            {'name': 'UE BOOM 2',   'mac_address': '88:C6:26:EE:BC:FE'}
            {'name': 'BLP9820',     'mac_address': '30:21:15:54:78:AA'}
        ]

    Raises: <none>
    """
    found_devices = bluetooth.get_connected_devices()
    return found_devices

@app.route('/connect_in/<mac_addr>')
def connect_input_device(mac_addr):
    """ connect_input_device

    Connects controller 0 to a MAC address. By convention, the controller 0 is reserved for the input device.

    Args:
        mac_addr (str)   : a MAC address, like 67:A8:88:C6:26:C3

    Returns:
        "OK" with status HTTP 200
        "Error" with status HTTP 500

    Raises: <none>
    """
    global controller, controller_idx, devices

    response = ""

    try:
        if isMacAddrInDevices(mac_addr, bluetooth.get_connected_devices()):
            return "device already connected", 200

        process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

        # select /dev/hci0 for this connection
        response += f"select controllers[0] = {controllers[0]}\n"
        logger.info(f"select controllers[0] = {controllers[0]}\n")
        process.stdin.write(f"select {controllers[0]}\n")
        process.stdin.flush()

        # disconnect device if it is already connected
        if 0 in devices.keys():
            response += f"controllers[0] is already connected to {devices[0]}\n"
            logger.info(f"controllers[0] is already connected to {devices[0]}")
            response += f"disconnect {devices[0]}\n"
            logger.info(f"disconnect {devices[0]}")
            process.stdin.write(f"disconnect {devices[0]}")
            process.stdin.flush()
            sleep(5)

        # scan for a few seconds
        process.stdin.write("scan on\n")
        process.stdin.flush()
        sleep(2)

        # pair with device only if not already paired
        if not isMacAddrInDevices(mac_addr, bluetooth.get_paired_devices()):
            sleep(2)
            response += f"device {mac_addr} was not paired\n"
            response += f"pair {mac_addr}\n"
            logger.info(f"pair {mac_addr}\n")
            process.stdin.write(f"pair {mac_addr}\n")
            process.stdin.flush()
            sleep(7)
            process.stdin.write(f"yes\n")
            process.stdin.flush()
            sleep(3)
        else:
            response += f"device {mac_addr} is already paired\n"

        # connect
        response += f"connect {mac_addr}\n"
        logger.info(f"connect {mac_addr}\n")
        process.stdin.write(f"connect {mac_addr}\n")
        process.stdin.flush()
        out, err = process.communicate()
        response += out

        # wait for a few seconds before confirmation
        sleep(4)
        if isMacAddrInDevices(mac_addr, bluetooth.get_connected_devices()):
            devices[0] = mac_addr
            return "OK", 200
        else:
            return response, 500

    except Exception as e:
        response += repr(e)
        return response, 500


@app.route('/connect_out/<mac_addr>')
def connect_output_device(mac_addr):
    """ connect_output_device

    Connects controller x to a MAC address.

    Args:
        mac_addr (str)   : a MAC address, like 67:A8:88:C6:26:C3

    Returns:
        "OK" with status HTTP 200
        "Error" with status HTTP 500

    Raises: <none>
    """
    global controller, controller_idx, devices

    response = ""

    try:
        process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

        response += f"select controller[{controller_idx}] = {controllers[controller_idx]}\n"
        logger.info(f"select controller[{controller_idx}] = {controllers[controller_idx]}\n")
        process.stdin.write(f"select {controllers[controller_idx]}\n")
        process.stdin.flush()

        # disconnect device if it is already connected to another bluetooth controller
        logger.info(f"is {controller_idx} in {devices.keys()} : {controller_idx in devices.keys()}")
        if controller_idx in devices.keys():
            response += f"controllers[{controller_idx}] is already connected to {devices[controller_idx]}"
            logger.info(f"controllers[{controller_idx}] is already connected to {devices[controller_idx]}")
            response += f"disconnect {devices[controller_idx]}"
            logger.info(f"disconnect {devices[controller_idx]}")
            process.stdin.write(f"disconnect {devices[controller_idx]}")
            process.stdin.flush()
            sleep(5)

        # scan for a few seconds
        process.stdin.write("scan on\n")
        process.stdin.flush()
        sleep(3)

        if not isMacAddrInDevices(mac_addr, bluetooth.get_paired_devices()):
            response += f"device {mac_addr} was not paired\n"
            response += f"pair {mac_addr}\n"
            logger.info(f"pair {mac_addr}\n")
            process.stdin.write(f"pair {mac_addr}\n")
            process.stdin.flush()
            sleep(6)
        else:
            response += f"device {mac_addr} is already paired\n"

        # connect
        response += f"connect {mac_addr}\n"
        logger.info(f"connect {mac_addr}\n")
        process.stdin.write(f"connect {mac_addr}\n")
        process.stdin.flush()

        # wait for a few seconds before confirmation
        sleep(4)
        if isMacAddrInDevices(mac_addr, bluetooth.get_connected_devices()):
            devices[controller_idx] = mac_addr
            controller_idx += 1
            logger.info(f"controller_idx set to {controller_idx}")
            beep()
            return "OK", 200
        else:
            return "Error", 500

    except Exception as e:
        response += repr(e)
        return response, 500


@app.route('/reset_in')
def reset_input_device():
    """ reset_input_device

    Disconnect / remove the input device i.e. /dev/hci0

    Args: <none>

    Returns:
        "OK" with status HTTP 200
        "Error" with status HTTP 500

    Raises: <none>
    """
    global controller, controller_idx, devices

    response = ""
    try:

        # input device is already disconnected
        if 0 not in devices.keys():
            return "OK", 200

        process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

        response += f"select {controllers[0]}\n"
        logger.info(f"select {controllers[0]}\n")
        process.stdin.write(f"select {controllers[0]}\n")
        process.stdin.flush()

        # if request.args.get('hard'):
        #     response += f"remove {devices[0]}\n"
        #     process.stdin.write(f"remove {devices[0]}\n")
        # else:
        response += f"disconnect {devices[0]}\n"
        logger.info(f"disconnect {devices[0]}\n")
        process.stdin.write(f"disconnect {devices[0]}\n")
        process.stdin.flush()
        sleep(1)

        out, err = process.communicate()
        response += out

        if devices[0] not in bluetooth.get_connected_devices():
            devices.pop(0)
            return "OK", 200
        else:
            return response, 500

    except Exception as e:
        response += repr(e)
        return response, 500


@app.route('/reset_out')
def reset_output_device():
    """ reset_output_device

    Disconnect or remove all output devices i.e. /dev/hci1, /dev/hci2, /dev/hci3,...
    without disconneting the input device.
    
    Args: <none>

    Returns:
        "OK" with status HTTP 200
        "Error" with status HTTP 500

    Raises: <none>
    """

    global controller, controller_idx, devices

    response = ""
    try:
        process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

        input_device = devices[0]
        for c in controllers[1:]:
            response += f"select {c}"
            logger.info(f"select {c}")
            process.stdin.write(f"select {c}\n")
            process.stdin.flush()

            for d in bluetooth.get_connected_devices():
                d = d["mac_address"].decode()
                if d != input_device:

                    #if request.args.get('hard'):
                    logger.info(f"remove {d}")
                    response += f"remove {d}\n"
                    process.stdin.write(f"remove {d}\n")
                    process.stdin.flush()
                    sleep(1)
                    #else:
                    #    response += f"remove {devices[0]}\n"
                    #    process.stdin.write(f"remove {devices[0]}\n")


        out, err = process.communicate()
        print(out)

        still_connected = bluetooth.get_connected_devices()
        if len(still_connected) == 1 and isMacAddrInDevices(input_device, still_connected):
            return "OK", 200
        else:
            return "Error", 500

    except Exception as e:
        response += repr(e)
        return response, 500




#------------------------------------
#          useful functions
#------------------------------------
def isMacAddrInDevices(mac_addr, devices):
    """ isMacAddrInDevices

    Opens a vlc subprocess for playing a beep audio file.
    This is used as a confirmation that a Bluetooth device has be properly connected.

    Args:
        mac_addr (str)   : a MAC address, like 67:A8:88:C6:26:C3
        devices  (array) : a JSON array of Bluetooth devices, returned by bluetool
                           (for an obscure reason, all string values are encoded in binary)

    Returns:
        True / False
    
    Raises: <none>
    """
    for d in devices:
        if mac_addr.encode() in d.values():
            return True
    return False


def beep():
    """ beep

    Opens a vlc subprocess for playing a beep audio file.
    This is used as a confirmation that a Bluetooth device has be properly connected.

    Args: <none>

    Returns: <none>

    Raises: <none>
    """
    subprocess.Popen(f"(cvlc /home/pi/bluebox/beep_6sec.wav &) >/dev/null 2>&1", shell=True)




#-----------------------
#         run
#-----------------------
# run as ./app.py
if __name__ == '__main__':
    from sys import argv
    app.run(host=argv[1]) if len(argv)>1 else app.run(host="192.168.0.142")

# or run with
# flask run --host "$(hostname -I | cut -d ' ' -f 1)"

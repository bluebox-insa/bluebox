#!/usr/bin/python3
"""
Bluebox server

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


In order to verify the proper Bluetooth and PulseAudio configuration, these commands could be executed:
This configuration is erased at shutdown and rewrittent at boot, it is therefore important to verify it.

    # verify that the bluetooth controller /dev/hci0 has been set to sink audio mode
    check_output("hciconfig hci0 class | grep -q 0x200420", shell=True)

    # verify that the combined sink
    check_output("pactl list sinks | grep -q bluebox_combined", shell=True)

The Bluebox may not work properly if an audio cable is wired in when it boots.
"""



#---------------------------
#          imports
#---------------------------
import subprocess, io, logging
logging.getLogger("bluetool").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.INFO)
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
LOGFILE                   ="/home/pi/logs.log"
handler                   = logging.FileHandler(LOGFILE)
logger.addHandler(handler)

# string handler
log_capture_string        = io.StringIO()
handler2                  = logging.StreamHandler(log_capture_string)
logger.addHandler(handler2)

app                       = Flask(__name__)
FlaskJSON(app)

# bluetool handler, used only to scan nearby bluetooth devices or retrieve currently connected bluetooth devices
bluetooth                 = Bluetooth()

# list of MAC addresses of the bluetooth controllers on the Raspberry Pi
# controllers[0]          = /dev/hci0,   controllers[1] = /dev/hci1 and so on
controllers               = subprocess.check_output('hcitool dev | grep -o \"[[:xdigit:]:]\{11,17\}\"', shell=True).decode().split('\n')[:-1]
controllers.reverse()
current_controller        = 1

connections               = {}
pairings                  = []
# controller_index        => mac_address




#---------------------------
#          routes
#---------------------------
@app.before_request
def before_request():
    """
    A bluetooth dongle may be plugged or unplugged at any time.
    To avoid errors, we should refresh the list of controllers before processing any request.
    This function does it, thanks to the Flask decorator @before_request
    """
    global controllers

    logger.info("%s %s" % (request.method, request.path))

    old_controllers = controllers
    controllers = subprocess.check_output('hcitool dev | grep -o \"[[:xdigit:]:]\{11,17\}\"', shell=True).decode().split('\n')[:-1]
    controllers.reverse()
    if controllers != old_controllers:
        logger.info(f"controllers updated to {controllers}")

    #on vérifie la correspondance entre connections et bluetooth.get_connected_devices
    # bluetool_devices = bluetooth.get_connected_devices()
    # compare lengths
    # assert len(connections) == len(bluetool_devices), f"len(connections) = {len(devices)} is not equal to len(bluetool_devices) = {len(bluetool_devices)} as expected"
    # for conn in connections:
    #     assert is_mac_addr_in_devices(conn["device_mac"], bluetool_devices), f"bluetool_devices = {bluetool_devices} doesn't contain conn[device_mac] = {conn["device_mac"]} as expected"


@app.after_request
def after_request(response):
    """ 
    Log results after request.

    Args: response (flask.Response)
    Returns: response (flask.Response)
    """
    if response.status_code == 200:
        logger.info(f"==> OK, 200")
    else:
        logger.error(f"==> error {response.status_code}")    
    logger.info(f"==> {response.data}\n") if response.data.decode("utf-8") != "OK" else None
    # log_contents = log_capture_string.getvalue()
    # log_capture_string.close()
    return response


@app.route('/')
def status():
    return "OK", 200


@app.route('/scan')
@as_json
def scan_for_bluetooth_devices():
    """
    Performs a scan of nearby bluetooth devices by calling the bluetool library (i.e. bluez).
    Devices must be in DISCOVERABLE state to be detected.
    The scan is performed with any of the bluetooth controllers and takes ~3 seconds.
    The scan cannot distinguish output devices (e.g. Bluetooth speakers) from input devices (e.g. smartphones).
    During our tests, the scan also detected LE Bluetooth devices.
    Sometimes a device name cannot be retrieved, so it is marked <unknown>.

    Returns:
        a JSON array of the devices found, for instance
        [
            {'name': 'Redmi',       'mac_address': '20:34:FB:A5:11:E8'}
            {'name': 'UE BOOM 2',   'mac_address': '88:C6:26:EE:BC:FE'}
            {'name': '<unknown>',   'mac_address': '67:A8:88:C6:26:C3'}
        ]
    """
    bluetooth.scan()
    found_devices = list(set(bluetooth.get_available_devices()))
    return found_devices, 200



@app.route('/connect/<mac_addr>')
def connect_to_device(mac_addr):
    """
    Connects controller X to a MAC address. By convention, the controller 0 is reserved for the input device.

    Args:
        mac_addr (str)   : a MAC address, like 67:A8:88:C6:26:C3
    Returns:
        "OK" with status HTTP 200
        "Error" with status HTTP 500
    """
    global connections

    try:
        controller_index = get_available_controller(mac_addr)

        if mac_addr in connections.values():
            return "device already connected", 200

        proc = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
        send_command(proc, f"select {controllers[controller_index]}")

        # scan
        send_command(proc, "scan on", 3)

        # pair
        if {"controller_index" : controller_index, "mac_addr" : mac_addr} not in pairings:
            send_command(proc, f"pair {mac_addr}", 7)
            send_command(proc, "yes", 3)

        # connect
        send_command(proc, f"connect {mac_addr}", 4)
        assert is_device_connected(mac_addr), f"connecting input {mac_addr} failed"

        # append to connections and pairings
        connections[controller_index] = mac_addr
        pairings.append({"controller_index" : controller_index, "mac_addr" : mac_addr})

        return "OK", 200

    except Exception as e:
        logger.error(e)
        return response, 500


@app.route('/connect_failed')
def connect_failed():
    """
    Returns:
        "OK" with status HTTP 200
        "Error" with status HTTP 500
    """
    global current_controller, connections

    response = ""

    try:
        current_controller -= 1
        logging.info(f"current_controller set back to {current_controller}")
        connections.pop(current_controller)
        return "OK", 200

    except Exception as e:
        logger.error(e)
        return response, 500


@app.route('/reset_<target>')
def reset(target):
    """
    Disconnect or remove the input device i.e. /dev/hci0
    Disconnect or remove all output devices i.e. /dev/hci1, /dev/hci2, /dev/hci3,...
    without disconneting the input device.

    Returns:
        "OK" with status HTTP 200
        "Error" with status HTTP 500
    """
    global current_controller, connections

    try:
        if target == "in":
            controller_indexes = [0]
        else:
            controller_indexes = [k for k in range(1,len(controllers))]
        logger.debug(f"indexes to delete = {controller_indexes}")

        proc = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

        for i in controller_indexes:
            send_command(proc, f"select {controllers[i]}")

            if request.args("hard"):
                send_command(proc, f"remove {connections[i]}", 1)
            else:
                send_command(proc, f"disconnect {connections[i]}", 1)

        sleep(1)
        for i in controller_indexes:
            assert not is_device_connected(connections[i]), f"disconnecting connections[{i}] ({connections[i]}) failed"
            connections.pop(i)
        
        return "OK", 200

    except Exception as e:
        logger.error(e)
        return response, 500


@app.route('/beep')
def beep():
    """
    Opens a vlc subprocess for playing a beep audio file.
    This is used as a confirmation that a Bluetooth device has be properly connected.
    """
    logger.info("Beeping...")
    subprocess.Popen(f"(cvlc /home/pi/bluebox/beep/beep_6sec.wav &) >/dev/null 2>&1", shell=True)




#------------------------------------
#          useful functions
#------------------------------------
def is_mac_addr_in_devices(mac_addr, devices):
    """
    Args:
        mac_addr (str)   : a MAC address, like 67:A8:88:C6:26:C3
        devices  (array) : a JSON array of Bluetooth devices, returned by bluetool
                           (for an obscure reason, all string values are encoded in binary)
    Returns:
        True / False
    """
    for d in devices:
        if mac_addr.encode() in d.values():
            return True
    return False

def is_device_connected(mac_addr):
    return is_mac_addr_in_devices(mac_addr, bluetooth.get_connected_devices())

def is_device_paired(mac_addr):
    return is_mac_addr_in_devices(mac_addr, bluetooth.get_paired_devices())

def send_command(process, command, wait_seconds=0):
    """
    Sends a command to a currently opened process and waits for x seconds.

    Args:
        process (subprocess.Process) : a bluetoothctl process
        command (str)                : a command understood by bluetoothctl
        wait_seconds (int)           : number of seconds to wait
    """
    logger.info(command)
    process.stdin.write(command + "\n")
    process.stdin.flush()
    if wait_seconds > 0:
        sleep(wait_seconds)


def get_available_controller(mac_addr, input_device=False):
    """
        Re
    """
    if input_device:
        controller_index = 0
    else:
        controller_index = current_controller

    if controller_index in connections.keys():
        raise Exception(f"controllers[0] is already connected to {connections[controller_index]}")
        logger.info()
        send_command(proc, f"disconnect {connections[controller_index]}", 5)



#-----------------------
#         run
#-----------------------
# run as ./app.py
if __name__ == '__main__':
    from sys import argv
    app.run(host=argv[1]) if len(argv)>1 else app.run(host="192.168.0.142")
    print(f"BlueBox server launched.\nExecute `tail -f {LOGFILE}` to see logs")
# or run with
# flask run --host "$(hostname -I | cut -d ' ' -f 1)"

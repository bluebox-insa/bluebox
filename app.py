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
import subprocess, io, logging, re
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

    logger.info("%s %s" % (request.method, request.full_path))

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

    logger.info(f"==> {response.data}") if response.data.decode() else None

    if response.status_code == 200:
        logger.info(f"==> OK, 200\n")
    else:
        logger.error(f"==> Error {response.status_code}\n")
        log_contents = log_capture_string.getvalue()
        response.data = log_contents
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
    found_devices = bluetooth.get_available_devices(unique_values=True)
    return found_devices, 200


@app.route('/devices')
@as_json
def get_devices():
    """
    Retrieves currently connected bluetooth devices.
    The scan cannot distinguish output devices (e.g. Bluetooth speakers) from input devices (e.g. smartphones).
    Returns:
        a JSON array of the devices found, for instance
        [
            {'name': 'Redmi',       'mac_address': '20:34:FB:A5:11:E8'}
            {'name': 'UE BOOM 2',   'mac_address': '88:C6:26:EE:BC:FE'}
            {'name': '<unknown>',   'mac_address': '67:A8:88:C6:26:C3'}
        ]
    """
    found_devices = bluetooth.get_connected_devices()
    return found_devices, 200

@app.route('/connect_<target>/<mac_addr>')
def connect_to_device(target, mac_addr):
    """
    Connects controller X to a MAC address. By convention, the controller 0 is reserved for the input device.
    Args:
        mac_addr (str)   : a MAC address, like 67:A8:88:C6:26:C3
    Returns:
        "OK" with status HTTP 200
        "Error" with status HTTP 500
    """
    global connections
    global bluetooth

    try:

        is_input = target == "input"
        controller_index = get_available_controller(mac_addr, is_input)

        if mac_addr in connections.values():
            return "device already connected", 200

        #handle  bt connection
        is_sink=not is_input
        device_connection(mac_addr=mac_addr ,controller_addr=controllers[controller_index],is_sink=is_sink)
        
        """
        if is_input:
            #bluetooth.connect(mac_addr)
            device_connection(mac_addr=mac_addr ,controller_addr=controllers[controller_index],is_sink=is_sink)
        else:
            device_connection(mac_addr=mac_addr ,controller_addr=controllers[controller_index],is_sink=is_sink)
        """

        # append to connections and pairings
        connections[controller_index] = mac_addr
        pairings.append({"controller_index" : controller_index, "mac_addr" : mac_addr})

        beep()
        return "", 200

    except Exception as e:
        '''
        if proc is not None:
            # get detailed output from bluetoothctl
            out, err = proc.communicate()

            # filter useless messages from output
            out = re.sub('.*CHG.*\n', '', out)
            out = re.sub('  [0-9a-f ]{9,}.*\n', '', out)
            out = re.sub('.*\\[0;94m\\[.+\\].*\\[0m# \n', '', out)
            out = re.sub('\n\n', '\n', out)
            out = "-----------------------------------------------------\n"+out
            out += "-----------------------------------------------------"

            # log output
            logger.error("\n            ** bluetoothctl output **\n" + out)

            #x = re.search('.*\\[0;94m\\[.+\\].*\\[0m# \n', out)
            #if x:
            #    print("SUCCESS")
            #    print(x)
            #    logger.error(out2) if out2 != out else None
            #else:
            #    print("FAILED TO MATCH")
            if err:
                logger.error(err)
        '''
        logger.exception(e)
        return "", 500


@app.route('/failed/<mac_addr>')
def connection_failed(mac_addr):
    """
    Returns:
        "OK" with status HTTP 200
        "Error" with status HTTP 500
    """
    global connections

    try:
        ele = [key for key,value in connections.items() if value == mac_addr][0]
        connections.pop(ele)
        logging.info(f"{mac_addr} removed from connections (it is now size {len(connections)})")
        return "", 200

    except IndexError as e:
        logger.exception(e)
        logger.error(f"Tried to remove mac_addr {mac_addr} but this address was not present in connections = {connections} as expected")
        return "", 200

    except Exception as e:
        logger.exception(e)
        return "", 500


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
        #select controller
        if target == "input":
            controller_indexes = [controllers[0]]
        else:
            controller_indexes = controllers[1:]
        logger.info(f"chosen controllers = {controller_indexes}")

        #reset controllers
        for controller_addr in controller_indexes:
            logger.info(f"Start RESET controller : {controller_addr}")
            reset_controller(controller_addr=controller_addr)
            logger.info(f"End RESET controller : {controller_addr}")

        '''
        try:
            remove_devices = request.args.get("hard") is not None
        except RuntimeError:
            remove_devices = True

        proc = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)

        devices = bluetooth.get_connected_devices(encode=False, unique_values=True)
        for d in devices:
            for c in controller_indexes:
                select_controller(bt_process=proc,controller_addr=c)
                #send_command(proc, f"select {c}")
                if remove_devices:
                    remove_device(bt_process=proc,mac_addr=d['mac_address'])
                    #send_command(proc, f"remove {d['mac_address']}", 1)
                else:
                    disconnect_device(bt_process=proc,mac_addr=d['mac_address'])
                    #send_command(proc, f"disconnect {d['mac_address']}", 1)
                connections.pop(d['mac_address']) if d['mac_address'] in connections.keys() else None
            sleep(1)
        '''
        devices = bluetooth.get_connected_devices()
        
        #assert len(devices) == 0, f"devices is of size {len(devices)} but was expected to be empty. Error reset with {devices}"
        connections.clear()
        
        return "", 200

    except Exception as e:
        logger.exception(e)
        return "", 500


@app.route('/beep')
def beep():
    """
    Opens a vlc subprocess for playing a beep audio file.
    This is used as a confirmation that a Bluetooth device has be properly connected.
    """
    try:
        logger.info("Beeping...")
        subprocess.Popen(f"(cvlc /home/pi/bluebox/beep/beep_6sec_2.wav &) >/dev/null 2>&1", shell=True)
        sleep(2)
        return "", 200
    except Exception as e:
        logger.exception(e)
        return "", 500




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
    logger.info(f"Searching {mac_addr} in size {len(devices)} array {devices}")
    for d in devices:
        if mac_addr.encode() in d.values():
            logger.info(f"is {mac_addr} in array : True")
            return True
        else:
            logger.info(f"is {mac_addr} in array : False")
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
        logger.info(f"Waiting {wait_seconds} seconds...")
        sleep(wait_seconds)


def get_available_controller(mac_addr, is_input=False):
    """
        Re
    """

    global current_controller

    if is_input:
        controller_index = 0

    else:
        l = [k for k in range(1, len(controllers)) if k not in connections.keys()]
        if len(l) == 0:
            raise NoAvailableControllersError(f"There is {len(controllers)} controllers.\nAnd {len(connections.keys)} busy controllers: {connections.keys()}.")
        controller_index = l[0]

    if controller_index in connections.keys():
        raise NoAvailableControllersError(f"controllers[{controller_index}] is already connected to {connections[controller_index]}")
        # send_command(proc, f"disconnect {connections[controller_index]}", 5)
    logger.info(f"Found available controller {controller_index} controller_list is {controllers}")
    return controller_index

#------------------------------------
#          New bt connection functions
#------------------------------------

def select_controller(bt_process,controller_addr):
    bt_process.stdin.write("select "+controller_addr+"\n")
    bt_process.stdin.flush()

def discover_device(bt_process,mac_addr):
    bt_process.stdin.write("scan on\n")
    bt_process.stdin.flush()
    for line in iter(bt_process.stdout.readline,"\n"):
        if mac_addr in line:
            logger.info("DEVICE SCAN IS OK")
            break


def connect_device(bt_process,mac_addr):
    bt_process.stdin.write("connect "+mac_addr+"\n")
    bt_process.stdin.flush()
    for line in iter(bt_process.stdout.readline,"\n"):
        #logger.info(f"{line}")
        if "Connection successful" in line:
            logger.info(f"DEVICE {mac_addr} IS CONNECTED")
            bt_process.stdin.write("exit\n")
            bt_process.stdin.flush()
            break
        

def disconnect_device(bt_process,mac_addr):
    bt_process.stdin.write("disconnect "+mac_addr+"\n")
    bt_process.stdin.flush()
    for line in iter(bt_process.stdout.readline,"\n"):
        if "Successful disconnected" in line:
            logger.info(f"DEVICE {mac_addr} IS DISCONNECTED")
            break

def pair_device(bt_process,mac_addr):
    bt_process.stdin.write("pair "+mac_addr+"\n")
    bt_process.stdin.flush()
    for line in iter(bt_process.stdout.readline,"\n"):
        
        if "Pairing successful" in line:
            logger.info(f"DEVICE {mac_addr} PAIR OK")
            break
        elif "org.bluez.Error.AlreadyExists" in line:
            #need to remove device
            remove_device(bt_process,mac_addr)
            #reload pairing mode
            bt_process.stdin.write("pair "+mac_addr+"\n")
            bt_process.stdin.flush()
    

def remove_device(bt_process,mac_addr):
    bt_process.stdin.write("remove "+mac_addr+"\n")
    bt_process.stdin.flush()
    for line in iter(bt_process.stdout.readline,"\n"):
        if "Device has been removed" in line:
            logger.info(f"DEVICE {mac_addr} has been removed")
            break
        
def sink_connection(mac_addr,controller_addr,process):
    discover_device(process,mac_addr)
    pair_device(process,mac_addr)
    connect_device(process,mac_addr)

def device_connection(mac_addr,controller_addr,is_sink):
    process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,text=True)
    select_controller(process,controller_addr)
    if is_sink:
        #connect to speaker
        sink_connection(mac_addr,controller_addr,process)
    else:
        #avoid pin request mode
        select_no_pin_agent_mode(bt_process=process)
        #connect to smartphone
        sink_connection(mac_addr,controller_addr,process)



#smartphone connection no pin request mode 

def select_no_pin_agent_mode(bt_process):
    set_agent_off(bt_process)
    set_agent_noInputOutput(bt_process)
    set_default_agent(bt_process)
    

def set_agent_off(bt_process):
    bt_process.stdin.write("agent off\n")
    bt_process.stdin.flush()
    for line in iter(bt_process.stdout.readline,"\n"):
        if "Agent unregistered" in line:
            logger.info(f"AGENT unregistered")
            break


def set_agent_noInputOutput(bt_process):
    bt_process.stdin.write("agent NoInputNoOutput\n")
    bt_process.stdin.flush()
    for line in iter(bt_process.stdout.readline,"\n"):
        if "Agent registered" in line:
            logger.info(f"Agent registered")
            break

def set_default_agent(bt_process):
    bt_process.stdin.write("default-agent\n")
    bt_process.stdin.flush()
    for line in iter(bt_process.stdout.readline,"\n"):
        if "Default agent request successful" in line:
            logger.info(f"Default Agent request sucessful")
            break

#reset functions using bluetoothctl
def get_device_list(process,controller_addr):
    process.stdin.write("paired-devices \n")
    process.stdin.flush()
    process.stdin.write("help \n")
    process.stdin.flush()
    p = re.compile(r'(?:[0-9a-fA-F]:?){12}')
    device_list=[]
    for line in iter(process.stdout.readline,"\n"):
        if "help" in line:
            break
        if not len(re.findall(p, line)):
            #empty list
            pass
        else:
            device_list.append(re.findall(p, line)[0])
    device_list=[mac_addr for mac_addr in device_list if mac_addr!=controller_addr]
    logger.info(f"list of devices to remove and/or disconnect {device_list}")
    return device_list

def reset_controller(controller_addr):
    process = subprocess.Popen(['bluetoothctl'], stdin=subprocess.PIPE, stdout=subprocess.PIPE,text=True)
    select_controller(process,controller_addr)
    device_list=get_device_list(process=process,controller_addr=controller_addr)
    for mac_addr in device_list:
        #try to disconnect device 
        disconnect_device(bt_process=process,mac_addr=mac_addr)
        #try to remove device
        remove_device(bt_process=process,mac_addr=mac_addr)




class NoAvailableControllersError(Exception):
    pass

#-----------------------
#         run
#-----------------------
# run as ./app.py
print(f"BlueBox server launched.\nExecute `tail -f {LOGFILE}` to see logs")
print(f"Found {len(controllers)} controllers: {controllers}")
devices_at_init = bluetooth.get_connected_devices(unique_values=True)
print(f"Found {len(devices_at_init)} devices: {devices_at_init}")
if len(devices_at_init)>0:
    reset("output")
    sleep(3)
    reset("input")
print()


if __name__ == '__main__':

    from sys import argv
    app.run(host=argv[1]) if len(argv)>1 else app.run(host="192.168.0.137")
# or run with
# flask run --host "$(hostname -I | cut -d ' ' -f 1)"

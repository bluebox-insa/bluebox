from subprocess import check_output

def get_controllers():
    controllers = []
    try:
        controllersRaw = check_output(["/usr/bin/bluetoothctl list"], shell=True).decode("utf-8")[:-1].split("\n").replace("Controller", "").replace("[default]", "").trim()
        for line in controllersRaw:
            controllers.append({
                "mac_addr" : line.split(" ")[0],
                "name" : line.split(" ")[1],
                })
    except Exception as e:
        print(f"Exception at {current_func()}: {e}")
    return controllers

def get_paired_devices():
    devices = []
    try:
        devices = check_output(["/usr/bin/bluetoothctl devices | /bin/grep -oE '(\\w\\w\\:){5}\\w\\w'"], shell=True).decode("utf-8")[:-1].split("\n")
    except Exception as e:
        print(f"Exception at {current_func()}: {e}")
    return devices


def is_device_connected(d):
    isConnected = False
    try:
        isConnected = check_output(["/usr/bin/bluetoothctl info "+d+" | /bin/grep -oE 'Connected:.*\n'"], shell=True).decode("utf-8")[:-1].replace("Connected: ", "") == "yes"
    except Exception as e:
        print(f"Exception at {current_func()}: {e}")
    return isConnected
    devices.append(state)


def get_connected_devices():
    devices = []
    for d in get_paired_devices():
        state = { "device" : d, "connected" : is_device_connected(d) }
        devices.append(state)
    return devices

def connect_device(d):
    from time import sleep

    # check current state
    state = currently_connected_to()
    if state != "":
        if state == d:
            # we are already connected
            return
        else:
            disconnect_device(d)

    # pair if needed
    if d not in get_paired_devices():
        try:
            check_output(["/bin/echo -e 'power on\nscan on' | /usr/bin/bluetoothctl"], shell=True)
            sleep(2)
            check_output([f"/bin/echo -e 'power on\npair {d}' | /usr/bin/bluetoothctl"], shell=True)
        except Exception as e:
            print(f"Exception at {current_func()}: {e}")

    # connect
    try:
        check_output([f"/bin/echo -e 'power on\nconnect {d}' | /usr/bin/bluetoothctl"], shell=True)
    except Exception as e:
        print(f"Exception at {current_func()}: {e}")

def disconnect_device(d):
    try:
        check_output(["/usr/bin/bluetoothctl disconnect "+d], shell=True)
    except Exception as e:
        print(f"Exception at {current_func()}: {e}")

def currently_connected_to():
    # pacmd list-cards: device.string = "88:C6:26:EE:BC:FE"
    # return "38:18:4C:BD:27:14"
    device = ""
    try:
        device = check_output(["/usr/bin/bluetoothctl info | /bin/grep -oE 'Device (\\w\\w\\:){5}\\w\\w'"], shell=True)[7:]
    except Exception as e:
        print(f"Exception at {current_func()}: {type(e)}")
    return device

def play_music(ipAddr, passwd="cookie", file="~/music.mp3"):
    try:
        check_output([f"/usr/bin/cvlc --intf http --http-host {ipAddr} --http-password {passwd} {file}"], shell=True)
    except Exception as e:
        print(f"Exception at {current_func()}: {e}")

def set_delay():
    pass
    # pactl set-port-latency-offset bluez_card.88_C6_26_EE_BC_FE unknown-output 1000000
    # pactl set-card-profile        bluez_card.88_C6_26_EE_BC_FE off
    # pactl set-card-profile        bluez_card.88_C6_26_EE_BC_FE a2dp_sink
    #
    # pactl set-port-latency-offset bluez_card.30_21_15_54_78_AA handsfree-output 1000000
    # pactl set-card-profile        bluez_card.30_21_15_54_78_AA off
    # pactl set-card-profile        bluez_card.30_21_15_54_78_AA a2dp_sink


def current_func():
    from inspect import currentframe
    from gc import get_referrers
    frame = currentframe()
    code  = frame.f_code
    globs = frame.f_globals
    functype = type(lambda: 0)
    funcs = []
    for func in get_referrers(code):
        if type(func) is functype:
            if getattr(func, "__code__", None) is code:
                if getattr(func, "__globals__", None) is globs:
                    funcs.append(func)
                    if len(funcs) > 1:
                        return None
    return funcs[0] if funcs else None

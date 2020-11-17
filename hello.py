from flask import Flask
from flask_json import FlaskJSON, JsonError, json_response, as_json
from functions import *
from bluetooth import discover_devices

app = Flask(__name__)
FlaskJSON(app)

@app.route('/')
def hello():
    return 'Hello, World!'

@app.route('/devices')
@as_json
def get_devices():
    # ?scan ou ?paired ou ?connected
    # devicesRaw = discover_devices(lookup_names=True)
    devicesRaw = [('04:52:C7:D2:CA:E3', 'Bose Revolve SoundLink'), ('20:74:CF:09:54:02', 'TREKZ Titanium by AfterShokz'), ('38:18:4C:BD:27:14', 'WH-1000XM3'), ('88:C6:26:40:2C:2C', 'UE BOOM')]
    devices = []
    for addr, name in devicesRaw:
        devices.append({
            "mac_addr" : addr,
            "name" : name
        })
    return devices


@app.route('/connect/<mac_addr>', METHODS=["PUT"])
@as_json
def put_connect(mac_addr):
    devicesRaw = [('04:52:C7:D2:CA:E3', 'Bose Revolve SoundLink'), ('20:74:CF:09:54:02', 'TREKZ Titanium by AfterShokz'), ('38:18:4C:BD:27:14', 'WH-1000XM3'), ('88:C6:26:40:2C:2C', 'UE BOOM')]
    devices = []
    for addr, name in devicesRaw:
        devices.append({
            "mac_addr" : addr,
            "name" : name
        })
    return devices

@app.route('/controllers', methods = ['POST', 'GET'])
@as_json
def get_controllers():

    if request.method == "GET":
        controllers = []
        try:
            controllersRaw = check_output(["/usr/bin/bluetoothctl list"], shell=True).decode("utf-8")[:-1].replace("Controller", "").replace("[default]", "").strip().split("\n")
            for line in controllersRaw:
                controllers.append({
                    "mac_addr" : line.split(" ")[0],
                    "name" : line.split(" ")[1],
                    })
        except Exception as e:
            print(f"Exception at {current_func()}: {e}")
        return controllers

    else:
        pass

@app.route('/dashboard/<name>')
def dashboard(name):
   return 'welcome %s' % name

if __name__ == '__main__':
    app.run()
    # debug = True
    # host = ""
    # port = ""

    

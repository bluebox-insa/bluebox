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
def devices():
    devicesRaw = discover_devices(lookup_names=True)
    devices = []
    for addr, name in devicesRaw:
        devices.append({
            "mac_addr" : addr,
            "name" : name
        })
    return devices

# @app.route('/controllers')
# @as_json
# def get_controllers():
#     controllers = []
#     try:
#         controllersRaw = check_output(["/usr/bin/bluetoothctl list"], shell=True).decode("utf-8")[:-1].split("\n").replace("Controller", "").replace("[default]", "").trim()
#         for line in controllersRaw:
#             controllers.append({
#                 "mac_addr" : line.split(" ")[0],
#                 "name" : line.split(" ")[1],
#                 })
#     except Exception as e:
#         print(f"Exception at {current_func()}: {e}")
#     return controllers

if __name__ == '__main__':
    app.run()

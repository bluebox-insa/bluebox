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
            "MAC_addr" : addr,
            "name" : name
        })
    return devices

if __name__ == '__main__':
    app.run()

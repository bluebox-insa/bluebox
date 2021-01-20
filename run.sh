#!/bin/bash
cd "$(dirname "$0")"
export FLASK_ENV=development
export FLASK_APP=app.py
flask run --host=$(hostname -I | cut -d " " -f 1) --port=12345

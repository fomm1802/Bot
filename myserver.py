from flask import Flask, render_template
from threading import Thread
import datetime
import os
import json
import logging

app = Flask(__name__, template_folder='Web Bot/templates', static_folder='Web Bot/static')

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

start_time_path = "start_time.txt"
try:
    with open(start_time_path, "r") as file:
        start_time = datetime.datetime.fromisoformat(file.read().strip())
except (FileNotFoundError, ValueError):
    start_time = datetime.datetime.now()
    with open(start_time_path, "w") as file:
        file.write(start_time.isoformat())

def load_config():
    config_path = "config.json"
    try:
        with open(config_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise Exception("Config file not found")
    except json.JSONDecodeError:
        raise Exception("Error reading config file")

config = load_config()

@app.route('/')
def home():
    return render_template("home.html", start_time=start_time.timestamp())

@app.route('/notify_channel_id')
def get_notify_channel_id():
    return os.getenv("NOTIFY_CHANNEL_ID", "Not set")

@app.route('/bot_status')
def get_bot_status():
    return "Running" if os.getenv("BOT_STATUS") == "running" else "Not running"

@app.route('/reset_uptime')
def reset_uptime():
    global start_time
    start_time = datetime.datetime.now()
    with open(start_time_path, "w") as file:
        file.write(start_time.isoformat())
    return "Uptime reset successfully"

def run():
    app.run(host='0.0.0.0', port=8080)
    
def keep_alive():
    server = Thread(target=run)
    server.start()
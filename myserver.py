from flask import Flask, render_template, request
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

def get_server_config(guild_id):
    server_config_path = f"configs/{guild_id}.json"
    if os.path.exists(server_config_path):
        with open(server_config_path, "r") as file:
            return json.load(file)
    else:
        return {"notify_channel_id": None}

def count_servers_in_config_folder():
    config_folder_path = "configs"
    try:
        return len([file for file in os.listdir(config_folder_path) if file.endswith('.json')])
    except FileNotFoundError:
        return 0

@app.route('/')
def home():
    server_count = count_servers_in_config_folder()
    return render_template("home.html", start_time=start_time.timestamp(), server_count=server_count)

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

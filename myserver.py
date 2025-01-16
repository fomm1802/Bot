from flask import Flask, render_template, request
from threading import Thread
import datetime
import os
import json
import logging
import requests

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

GITHUB_API_URL = "https://api.github.com"
GITHUB_REPO = "username/repo"
GITHUB_FILE_PATH = "path/to/file"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

def update_github_file():
    url = f"{GITHUB_API_URL}/repos/{GITHUB_REPO}/contents/{GITHUB_FILE_PATH}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_info = response.json()
        sha = file_info['sha']
        content = "New file content"
        data = {
            "message": "Update file via bot",
            "content": content.encode('utf-8').decode('utf-8'),
            "sha": sha
        }
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            return "File updated successfully"
        else:
            return f"Error updating file: {response.status_code}"
    else:
        return f"Error fetching file: {response.status_code}"

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

@app.route('/update_github_file', methods=['POST'])
def update_github_file_route():
    return update_github_file()

def run():
    app.run(host='0.0.0.0', port=8080)
    
def keep_alive():
    server = Thread(target=run)
    server.start()

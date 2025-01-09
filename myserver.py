from flask import Flask, render_template, request
from threading import Thread
import datetime
import os
import json
import logging
import requests
from dotenv import load_dotenv

# Initialize Flask application
app = Flask(__name__, template_folder='Web Bot/templates', static_folder='Web Bot/static')

# Disable logging for Werkzeug
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Load environment variables
load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO = os.getenv("GITHUB_REPO")
GITHUB_API_URL = "https://api.github.com"

# Define paths
start_time_path = "start_time.txt"

# Load or initialize start_time
try:
    with open(start_time_path, "r") as file:
        start_time = datetime.datetime.fromisoformat(file.read().strip())
except (FileNotFoundError, ValueError):
    start_time = datetime.datetime.now()
    with open(start_time_path, "w") as file:
        file.write(start_time.isoformat())

# Load main config from GitHub
def load_config():
    config_file_path = "config.json"
    url = f"{GITHUB_API_URL}/repos/{GITHUB_REPO}/contents/{config_file_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()
            config_data = json.loads(content['content'])
            return config_data
        else:
            logging.error(f"❌ Error fetching config: {response.text}")
            return {}
    except Exception as e:
        logging.error(f"❌ Error reading config from GitHub: {e}")
        return {}

config = load_config()

# Load server-specific config from GitHub
def get_server_config(guild_id):
    server_config_path = f"configs/{guild_id}.json"
    url = f"{GITHUB_API_URL}/repos/{GITHUB_REPO}/contents/{server_config_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}

    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()
            return json.loads(content['content'])
        else:
            return {"notify_channel_id": None}
    except Exception as e:
        logging.error(f"❌ Error fetching server config: {e}")
        return {"notify_channel_id": None}

# Save server config to GitHub
def save_server_config_to_github(guild_id, config_data):
    server_config_path = f"configs/{guild_id}.json"
    url = f"{GITHUB_API_URL}/repos/{GITHUB_REPO}/contents/{server_config_path}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    # Get the current file information to update it
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            content = response.json()
            sha = content['sha']
            data = {
                "message": f"Update server config for {guild_id}",
                "sha": sha,
                "content": json.dumps(config_data).encode("utf-8").decode("utf-8")
            }
            response = requests.put(url, json=data, headers=headers)
            if response.status_code == 200:
                logging.info(f"✅ Server config for {guild_id} saved to GitHub.")
            else:
                logging.error(f"❌ Error saving server config: {response.text}")
        else:
            logging.error(f"❌ Error fetching server config: {response.text}")
    except Exception as e:
        logging.error(f"❌ Error saving to GitHub: {e}")

# Count server config files in the configs folder on GitHub
def count_servers_in_config_folder():
    url = f"{GITHUB_API_URL}/repos/{GITHUB_REPO}/contents/configs"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            files = response.json()
            return len([file for file in files if file['name'].endswith('.json')])
        else:
            logging.warning(f"⚠️ Error fetching config files from GitHub: {response.text}")
            return 0
    except Exception as e:
        logging.warning(f"⚠️ Error counting config files: {e}")
        return 0

# Flask routes
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
    try:
        with open(start_time_path, "w") as file:
            file.write(start_time.isoformat())
        return "Uptime reset successfully"
    except IOError as e:
        logging.error(f"❌ Failed to write start_time: {e}")
        return "Failed to reset uptime", 500

@app.route('/server_count')
def server_count():
    count = count_servers_in_config_folder()
    return str(count)

# Route to save server config to GitHub
@app.route('/save_server_config/<guild_id>', methods=['POST'])
def save_server_config(guild_id):
    config_data = request.json
    if not config_data:
        return "Invalid config data.", 400

    save_server_config_to_github(guild_id, config_data)
    return "Server config saved to GitHub."

# Flask app run function
def run():
    app.run(host='0.0.0.0', port=8080)

# Function to keep Flask app alive
def keep_alive():
    server = Thread(target=run)
    server.start()

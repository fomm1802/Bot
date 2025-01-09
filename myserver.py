from flask import Flask, render_template, request
from threading import Thread
import datetime
import os
import json
import logging
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Flask application
app = Flask(__name__, template_folder='Web Bot/templates', static_folder='Web Bot/static')

# Disable logging for Werkzeug
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Firebase setup
service_account_path = "serviceAccountKey.json"

try:
    # Load Firebase credentials and initialize app
    cred = credentials.Certificate(service_account_path)
    firebase_admin.initialize_app(cred)
    db = firestore.client()
    logging.info("✅ Firebase initialized successfully.")
except Exception as e:
    logging.error(f"❌ Error initializing Firebase: {e}")
    db = None

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

# Load main config
def load_config():
    config_path = "config.json"
    try:
        with open(config_path, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        logging.error("❌ Config file not found.")
        return {}
    except json.JSONDecodeError:
        logging.error("❌ Error reading config.json.")
        return {}

config = load_config()

# Load server-specific config
def get_server_config(guild_id):
    server_config_path = f"configs/{guild_id}.json"
    try:
        if os.path.exists(server_config_path):
            with open(server_config_path, "r") as file:
                return json.load(file)
    except json.JSONDecodeError:
        logging.error(f"❌ Error reading {server_config_path}.")
    return {"notify_channel_id": None}

# Save server-specific config to Firebase
def save_server_config_to_firebase(guild_id, config_data):
    if db:
        try:
            db.collection("server_configs").document(guild_id).set(config_data)
            logging.info(f"✅ Server config for {guild_id} saved to Firebase.")
        except Exception as e:
            logging.error(f"❌ Error saving server config to Firebase: {e}")

# Count server config files in the configs folder
def count_servers_in_config_folder():
    config_folder_path = "configs"
    try:
        return len([file for file in os.listdir(config_folder_path) if file.endswith('.json')])
    except FileNotFoundError:
        logging.warning("⚠️ Configs folder not found.")
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

# Route to save server config to Firebase
@app.route('/save_server_config/<guild_id>', methods=['POST'])
def save_server_config(guild_id):
    config_data = request.json
    if not config_data:
        return "Invalid config data.", 400

    save_server_config_to_firebase(guild_id, config_data)
    return "Server config saved to Firebase."

# Flask app run function
def run():
    app.run(host='0.0.0.0', port=8080)

# Function to keep Flask app alive
def keep_alive():
    server = Thread(target=run)
    server.start()

from flask import Flask, render_template, request, jsonify
from threading import Thread
import datetime
import os
import json
import logging
import requests
import base64

app = Flask(__name__, template_folder='Web Bot/templates', static_folder='Web Bot/static')

# ตั้งค่า logging เพื่อลดระดับการแสดงผล
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# กำหนด path ของไฟล์ start_time
start_time_path = "start_time.txt"
try:
    with open(start_time_path, "r") as file:
        start_time = datetime.datetime.fromisoformat(file.read().strip())
except (FileNotFoundError, ValueError):
    start_time = datetime.datetime.now()
    with open(start_time_path, "w") as file:
        file.write(start_time.isoformat())

# ฟังก์ชันดึง config ของ server
def get_server_config(guild_id):
    server_config_path = f"configs/{guild_id}.json"
    if os.path.exists(server_config_path):
        with open(server_config_path, "r") as file:
            return json.load(file)
    return {"notify_channel_id": None}

# ฟังก์ชันนับจำนวนไฟล์ในโฟลเดอร์ configs
def count_servers_in_config_folder():
    config_folder_path = "configs"
    try:
        return len([file for file in os.listdir(config_folder_path) if file.endswith('.json')])
    except FileNotFoundError:
        return 0

# GitHub API Configuration
GITHUB_API_URL = "https://api.github.com"
GITHUB_REPO = "fomm1802/Bot"
GITHUB_FOLDER_PATH = "configs/"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

# ฟังก์ชันอัปเดตไฟล์ใน GitHub
def update_github_file(file_path, new_content):
    url = f"{GITHUB_API_URL}/repos/{GITHUB_REPO}/contents/{file_path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        file_info = response.json()
        sha = file_info['sha']
        data = {
            "message": "Update file via bot",
            "content": base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
            "sha": sha
        }
        response = requests.put(url, headers=headers, json=data)
        if response.status_code == 200:
            return jsonify({"message": "File updated successfully"})
        else:
            return jsonify({"error": f"Error updating file: {response.status_code}"})
    else:
        return jsonify({"error": f"Error fetching file: {response.status_code}"})

# Route: หน้าแรก
@app.route('/')
def home():
    server_count = count_servers_in_config_folder()
    return render_template("home.html", start_time=start_time.isoformat(), server_count=server_count)

# Route: ตรวจสอบสถานะบอท
@app.route('/bot_status')
def get_bot_status():
    bot_status = "Running" if os.getenv("BOT_STATUS") == "running" else "Not running"
    return jsonify({"status": bot_status})

# Route: รีเซ็ต uptime
@app.route('/reset_uptime', methods=['POST'])
def reset_uptime():
    global start_time
    start_time = datetime.datetime.now()
    with open(start_time_path, "w") as file:
        file.write(start_time.isoformat())
    return jsonify({"message": "Uptime reset successfully"})

# Route: นับจำนวนเซิร์ฟเวอร์
@app.route('/server_count')
def server_count():
    count = count_servers_in_config_folder()
    return jsonify({"count": count})

# Route: อัปเดตไฟล์ใน GitHub
@app.route('/update_github_file', methods=['POST'])
def update_github_file_route():
    file_path = request.json.get('file_path')
    new_content = request.json.get('new_content')
    if not file_path or not new_content:
        return jsonify({"error": "Missing file_path or new_content"}), 400
    return update_github_file(file_path, new_content)

# ฟังก์ชันรันเซิร์ฟเวอร์ Flask
def run():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# ฟังก์ชัน keep_alive
def keep_alive():
    server = Thread(target=run)
    server.start()
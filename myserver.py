from flask import Flask
from threading import Thread
import datetime
import os
import json
import logging

app = Flask('')

# Disable Flask's default request logging
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

# Load start time from file or set to current time
try:
    with open("start_time.txt", "r") as file:
        start_time = datetime.datetime.fromisoformat(file.read().strip())
except (FileNotFoundError, ValueError):
    start_time = datetime.datetime.now()
    with open("start_time.txt", "w") as file:
        file.write(start_time.isoformat())

def load_config():
    """โหลดการตั้งค่าจากไฟล์ config.json"""
    try:
        with open("config.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise Exception("ไม่พบไฟล์ config.json")
    except json.JSONDecodeError:
        raise Exception("ไฟล์ config.json มีข้อผิดพลาดในการอ่านข้อมูล")

config = load_config()

@app.route('/')
def home():
    return f"""
    <html>
    <head>
        <title>Bot Status</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f0f0f0;
                color: #333;
                text-align: center;
                padding: 50px;
            }}
            h1 {{
                color: #4CAF50;
                font-size: 2.5em;
                text-shadow: 2px 2px 4px #aaa;
            }}
            p {{
                font-size: 1.2em;
                margin: 10px 0;
            }}
            .status {{
                color: #FF5733;
                font-weight: bold;
                text-shadow: 1px 1px 2px #aaa;
            }}
            .uptime {{
                color: #3498DB;
                font-weight: bold;
                text-shadow: 1px 1px 2px #aaa;
            }}
            .notify {{
                color: #9B59B6;
                font-weight: bold;
                text-shadow: 1px 1px 2px #aaa;
            }}
            .container {{
                background-color: #fff;
                border-radius: 10px;
                box-shadow: 0 0 20px rgba(0, 0, 0, 0.1);
                padding: 20px;
                max-width: 600px;
                margin: auto;
                transition: transform 0.3s;
            }}
            .container:hover {{
                transform: scale(1.05);
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Server is running</h1>
            <p>Uptime: <span id="uptime" class="uptime"></span></p>
            <p>Notify Channel ID: <span id="notify_channel_id" class="notify"></span></p>
            <p>Bot Status: <span id="bot_status" class="status"></span></p>
        </div>
        <script>
            function updateUptime() {{
                const startTime = new Date({start_time.timestamp()} * 1000);
                const now = new Date();
                const uptime = new Date(now - startTime);
                const days = Math.floor(uptime / (1000 * 60 * 60 * 24));
                const hours = uptime.getUTCHours();
                const minutes = uptime.getUTCMinutes();
                const seconds = uptime.getUTCSeconds();
                document.getElementById('uptime').innerText = 
                    `${{days}} days, ${{hours}} hours, ${{minutes}} minutes, ${{seconds}} seconds`;
            }}
            function updateNotifyChannelId() {{
                fetch('/notify_channel_id')
                    .then(response => response.text())
                    .then(data => {{
                        document.getElementById('notify_channel_id').innerText = data;
                    }});
            }}
            function updateBotStatus() {{
                fetch('/bot_status')
                    .then(response => response.text())
                    .then(data => {{
                        document.getElementById('bot_status').innerText = data;
                    }});
            }}
            setInterval(updateUptime, 1000);
            setInterval(updateNotifyChannelId, 1000);
            setInterval(updateBotStatus, 1000);
            updateUptime();
            updateNotifyChannelId();
            updateBotStatus();
        </script>
    </body>
    </html>
    """

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
    with open("start_time.txt", "w") as file:
        file.write(start_time.isoformat())
    return "Uptime reset successfully"

def run():
    app.run(host='0.0.0.0', port=8080)
    
def keep_alive():
    server = Thread(target=run)
    server.start()

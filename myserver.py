from flask import Flask, render_template, request, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache
from threading import Thread
import datetime
import os
import json
import logging
import requests
import base64
from functools import wraps
import hmac
import hashlib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('web.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Config class
class Config:
    def __init__(self):
        self.github_api_url = "https://api.github.com"
        self.github_repo = os.getenv("GITHUB_REPO", "fomm1802/Bot")
        self.github_folder_path = "configs/"
        self.github_token = os.getenv("GITHUB_TOKEN")
        self.api_secret = os.getenv("API_SECRET", "default-secret-key-change-me")
        self.rate_limit = os.getenv("RATE_LIMIT", "100 per minute")
        self.port = int(os.environ.get("PORT", 8080))
        self.cache_type = os.getenv("CACHE_TYPE", "simple")
        self.start_time_path = "start_time.txt"

        if not self.github_token:
            logger.warning("⚠️ GITHUB_TOKEN not set")
        if self.api_secret == "default-secret-key-change-me":
            logger.warning("⚠️ Using default API_SECRET")

    def get_github_headers(self):
        return {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

# Initialize Flask app
app = Flask(__name__, template_folder='Web Bot/templates', static_folder='Web Bot/static')
config = Config()

# Initialize rate limiter
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=[config.rate_limit]
)

# Initialize cache
cache = Cache(app, config={
    'CACHE_TYPE': config.cache_type,
    'CACHE_DEFAULT_TIMEOUT': 300
})

# Security decorator
def require_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({"error": "No API key provided"}), 401

        expected_signature = hmac.new(
            config.api_secret.encode(),
            request.get_data(),
            hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(api_key, expected_signature):
            return jsonify({"error": "Invalid API key"}), 403

        return f(*args, **kwargs)
    return decorated_function

class ServerConfigManager:
    def __init__(self, config_dir="configs"):
        self.config_dir = config_dir
        os.makedirs(config_dir, exist_ok=True)

    def get_config(self, guild_id):
        """Get server config with error handling"""
        try:
            path = os.path.join(self.config_dir, f"{guild_id}.json")
            if not os.path.exists(path):
                return {"notify_channel_id": None}

            with open(path, "r", encoding='utf-8') as file:
                return json.load(file)
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing error in {guild_id}.json: {str(e)}")
            self._backup_corrupted_file(guild_id)
            return {"notify_channel_id": None}
        except Exception as e:
            logger.error(f"❌ Error reading config for {guild_id}: {str(e)}")
            return {"notify_channel_id": None}

    def _backup_corrupted_file(self, guild_id):
        """Backup corrupted config file"""
        try:
            old_path = os.path.join(self.config_dir, f"{guild_id}.json")
            backup_path = os.path.join(self.config_dir, f"backup_{guild_id}_{int(datetime.datetime.now().timestamp())}.json")
            if os.path.exists(old_path):
                os.rename(old_path, backup_path)
                logger.info(f"✅ Created backup: {backup_path}")
        except Exception as e:
            logger.error(f"❌ Failed to create backup: {str(e)}")

    def count_servers(self):
        """Count server configs"""
        try:
            return len([f for f in os.listdir(self.config_dir) if f.endswith('.json')])
        except Exception as e:
            logger.error(f"❌ Error counting servers: {str(e)}")
            return 0

class GitHubManager:
    def __init__(self, config):
        self.config = config

    async def update_file(self, file_path, new_content):
        """Update file on GitHub with error handling"""
        try:
            url = f"{self.config.github_api_url}/repos/{self.config.github_repo}/contents/{file_path}"
            headers = self.config.get_github_headers()

            # Get existing file
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            file_info = response.json()
            sha = file_info['sha']

            # Update file
            data = {
                "message": "Update file via bot",
                "content": base64.b64encode(new_content.encode('utf-8')).decode('utf-8'),
                "sha": sha
            }

            response = requests.put(url, headers=headers, json=data)
            response.raise_for_status()

            logger.info(f"✅ Successfully updated {file_path} on GitHub")
            return {"message": "File updated successfully"}

        except requests.exceptions.RequestException as e:
            logger.error(f"❌ GitHub API error: {str(e)}")
            return {"error": f"GitHub API error: {str(e)}"}, 500
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            return {"error": "Internal server error"}, 500

# Initialize managers
server_config_manager = ServerConfigManager()
github_manager = GitHubManager(config)

# Routes
@app.route('/')
@cache.cached(timeout=60)
def home():
    """Home page with caching"""
    try:
        server_count = server_config_manager.count_servers()
        return render_template(
            "home.html",
            start_time=get_start_time().isoformat(),
            server_count=server_count
        )
    except Exception as e:
        logger.error(f"❌ Error in home route: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/bot_status')
@cache.cached(timeout=30)
def get_bot_status():
    """Get bot status with caching"""
    try:
        bot_status = "Running" if os.getenv("BOT_STATUS") == "running" else "Not running"
        return jsonify({"status": bot_status})
    except Exception as e:
        logger.error(f"❌ Error getting bot status: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/reset_uptime', methods=['POST'])
@require_api_key
def reset_uptime():
    """Reset uptime with authentication"""
    try:
        new_start_time = datetime.datetime.now()
        with open(config.start_time_path, "w") as file:
            file.write(new_start_time.isoformat())
        cache.delete('start_time')
        return jsonify({"message": "Uptime reset successfully"})
    except Exception as e:
        logger.error(f"❌ Error resetting uptime: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/server_count')
@cache.cached(timeout=60)
def server_count():
    """Get server count with caching"""
    try:
        count = server_config_manager.count_servers()
        return jsonify({"count": count})
    except Exception as e:
        logger.error(f"❌ Error getting server count: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

@app.route('/update_github_file', methods=['POST'])
@require_api_key
@limiter.limit("10 per minute")
def update_github_file_route():
    """Update GitHub file with rate limiting and authentication"""
    try:
        file_path = request.json.get('file_path')
        new_content = request.json.get('new_content')
        
        if not file_path or not new_content:
            return jsonify({"error": "Missing file_path or new_content"}), 400
            
        return github_manager.update_file(file_path, new_content)
    except Exception as e:
        logger.error(f"❌ Error updating GitHub file: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

def get_start_time():
    """Get start time with caching"""
    start_time = cache.get('start_time')
    if start_time is None:
        try:
            with open(config.start_time_path, "r") as file:
                start_time = datetime.datetime.fromisoformat(file.read().strip())
        except (FileNotFoundError, ValueError):
            start_time = datetime.datetime.now()
            with open(config.start_time_path, "w") as file:
                file.write(start_time.isoformat())
        cache.set('start_time', start_time)
    return start_time

def run():
    """Run Flask server"""
    try:
        app.run(host='0.0.0.0', port=config.port)
    except Exception as e:
        logger.error(f"❌ Server failed to start: {str(e)}")
        raise

def keep_alive():
    """Start server in background thread"""
    try:
        server = Thread(target=run)
        server.daemon = True  # Thread will be terminated when main program exits
        server.start()
        logger.info("✅ Web server started successfully")
    except Exception as e:
        logger.error(f"❌ Failed to start web server: {str(e)}")
        raise

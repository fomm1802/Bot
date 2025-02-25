import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
import logging
import aiohttp
import sys
from dotenv import load_dotenv
import time
import base64
import requests
from myserver import keep_alive

# ตั้งค่า logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

class Config:
    def __init__(self):
        self.prefix = os.getenv('BOT_PREFIX', '!')
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_repo = os.getenv('GITHUB_REPO', 'fomm1802/Bot')
        self.github_branch = os.getenv('GITHUB_BRANCH', 'main')
        self.presence_update_interval = int(os.getenv('PRESENCE_UPDATE_INTERVAL', '30'))

        if not self.github_token:
            logging.warning("⚠️ GITHUB_TOKEN not set in environment variables")

    def get_github_headers(self):
        return {
            "Authorization": f"Bearer {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }

    def get_github_url(self, guild_id):
        return f"https://api.github.com/repos/{self.github_repo}/contents/configs/{guild_id}.json"

class BotStatus:
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()
        self.status_index = 0
        self.status_list = [
            self._get_uptime_status,
            self._get_servers_status,
            self._get_members_status,
            self._get_help_status
        ]

    def _get_uptime(self):
        """Calculate bot uptime"""
        uptime_seconds = int(time.time() - self.start_time)
        hours = uptime_seconds // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        return f"{hours}h {minutes}m {seconds}s"

    async def _get_uptime_status(self):
        """Get uptime status"""
        return discord.Activity(
            type=discord.ActivityType.playing,
            name=f"Online for {self._get_uptime()}"
        )

    async def _get_servers_status(self):
        """Get servers count status"""
        server_count = len(self.bot.guilds)
        return discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{server_count} servers"
        )

    async def _get_members_status(self):
        """Get total members count status"""
        member_count = sum(guild.member_count for guild in self.bot.guilds)
        return discord.Activity(
            type=discord.ActivityType.watching,
            name=f"{member_count} members"
        )

    async def _get_help_status(self):
        """Get help command status"""
        return discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{config.prefix}help for commands"
        )

    async def update(self):
        """Update bot status"""
        try:
            status_func = self.status_list[self.status_index]
            activity = await status_func()
            await self.bot.change_presence(activity=activity)

            # Rotate to next status
            self.status_index = (self.status_index + 1) % len(self.status_list)

        except Exception as e:
            logging.error(f"❌ Failed to update presence: {str(e)}")
            # Set fallback status
            await self.bot.change_presence(
                activity=discord.Game(name=f"{config.prefix}help"),
                status=discord.Status.online
            )

# Initialize config
config = Config()

# ตั้งค่า Intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config.prefix, intents=intents)
bot.config = config

# Initialize bot status
bot_status = BotStatus(bot)

# Update presence task
@tasks.loop(seconds=config.presence_update_interval)
async def update_presence():
    await bot_status.update()

bot.update_presence = update_presence

class ServerConfig:
    DEFAULT_CONFIG = {
        "notify_channel_id": None,
        "welcome_message": "Welcome to the server!",
        "prefix": "!",
        "disabled_commands": [],
        "last_updated": None
    }

    def __init__(self, guild_id):
        self.guild_id = guild_id
        self.config_path = f"configs/{guild_id}.json"
        self.data = self.load()

    def load(self):
        """Load config from file with validation and backup"""
        if not os.path.exists(self.config_path):
            return self.DEFAULT_CONFIG.copy()

        try:
            with open(self.config_path, "r", encoding='utf-8') as file:
                data = json.load(file)

            # Validate and update missing fields
            for key, default_value in self.DEFAULT_CONFIG.items():
                if key not in data:
                    data[key] = default_value

            return data

        except json.JSONDecodeError as e:
            self._backup_corrupted_file()
            logging.error(f"❌ JSON parsing error in {self.guild_id}.json: {str(e)}")
            return self.DEFAULT_CONFIG.copy()

        except Exception as e:
            logging.error(f"❌ Error loading config for {self.guild_id}: {str(e)}")
            return self.DEFAULT_CONFIG.copy()

    def _backup_corrupted_file(self):
        """Create backup of corrupted config file"""
        if not os.path.exists(self.config_path):
            return

        backup_path = f"configs/backup_{self.guild_id}_{int(time.time())}.json"
        try:
            os.rename(self.config_path, backup_path)
            logging.info(f"✅ Created backup of corrupted config: {backup_path}")
        except OSError as e:
            logging.error(f"❌ Failed to create backup: {str(e)}")

    async def save(self):
        """Save config to both local file and GitHub"""
        self.data["last_updated"] = int(time.time())

        # Save locally first
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        try:
            with open(self.config_path, "w", encoding='utf-8') as file:
                json.dump(self.data, file, indent=4)
        except Exception as e:
            logging.error(f"❌ Failed to save local config: {str(e)}")
            return False

        # Then save to GitHub
        return await self.save_to_github()

    async def save_to_github(self, max_retries=3):
        """Save config to GitHub with retry mechanism"""
        url = config.get_github_url(self.guild_id)
        headers = config.get_github_headers()

        for attempt in range(max_retries):
            try:
                async with aiohttp.ClientSession() as session:
                    # Get existing file
                    async with session.get(url, headers=headers) as response:
                        if response.status == 200:
                            existing = await response.json()
                            sha = existing.get('sha')
                        else:
                            sha = None

                    # Prepare update data
                    data = {
                        "message": f"Update config for guild {self.guild_id}",
                        "content": base64.b64encode(json.dumps(self.data, indent=4).encode()).decode(),
                        "branch": config.github_branch,
                        "sha": sha
                    }

                    # Update file
                    async with session.put(url, headers=headers, json=data) as response:
                        if response.status in (200, 201):
                            logging.info(f"✅ Successfully updated GitHub config for guild {self.guild_id}")
                            return True
                        else:
                            error_text = await response.text()
                            logging.error(f"❌ GitHub update failed: {error_text}")

            except Exception as e:
                if attempt == max_retries - 1:
                    logging.error(f"❌ GitHub update failed after {max_retries} attempts: {str(e)}")
                    return False
                logging.warning(f"Retrying GitHub update ({attempt + 1}/{max_retries})")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

        return False

    def get(self, key, default=None):
        """Safely get config value"""
        return self.data.get(key, default)

    def set(self, key, value):
        """Set config value"""
        self.data[key] = value

    async def exists_on_github(self):
        """Check if config exists on GitHub"""
        url = config.get_github_url(self.guild_id)
        headers = config.get_github_headers()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    return response.status == 200
        except Exception as e:
            logging.error(f"❌ Failed to check GitHub config: {str(e)}")
            return False

# Global cache for server configs
server_configs = {}

class ExtensionManager:
    def __init__(self, bot):
        self.bot = bot
        self.loaded_extensions = set()
        self.extension_paths = {
            'events': 'events',
            'commands': 'commands'
        }

    async def load_all(self):
        """Load all extensions from configured paths"""
        for ext_type, path in self.extension_paths.items():
            await self.load_from_directory(ext_type, path)

    async def load_from_directory(self, ext_type, directory):
        """Load all extensions from a directory"""
        if not os.path.exists(directory):
            logging.warning(f"⚠️ Directory not found: {directory}")
            return

        for filename in os.listdir(directory):
            if filename.endswith('.py'):
                ext_name = f"{ext_type}.{filename[:-3]}"
                await self.load_extension(ext_name)

    async def load_extension(self, ext_name):
        """Load a single extension with error handling"""
        try:
            if ext_name in self.loaded_extensions:
                logging.warning(f"⚠️ Extension already loaded: {ext_name}")
                return

            await self.bot.load_extension(ext_name)
            self.loaded_extensions.add(ext_name)
            logging.info(f"✅ Successfully loaded {ext_name}")

        except Exception as e:
            logging.error(f"❌ Failed to load {ext_name}: {str(e)}")

    async def reload_all(self):
        """Reload all loaded extensions"""
        failed = []
        for ext_name in list(self.loaded_extensions):
            try:
                await self.bot.reload_extension(ext_name)
                logging.info(f"🔄 Reloaded {ext_name}")
            except Exception as e:
                logging.error(f"❌ Failed to reload {ext_name}: {str(e)}")
                failed.append(ext_name)
        return failed

    async def unload_all(self):
        """Unload all loaded extensions"""
        for ext_name in list(self.loaded_extensions):
            try:
                await self.bot.unload_extension(ext_name)
                self.loaded_extensions.remove(ext_name)
                logging.info(f"❌ Unloaded {ext_name}")
            except Exception as e:
                logging.error(f"❌ Failed to unload {ext_name}: {str(e)}")

# Initialize extension manager
extension_manager = ExtensionManager(bot)

class BotManager:
    def __init__(self, bot, extension_manager):
        self.bot = bot
        self.extension_manager = extension_manager

    async def setup(self):
        """Setup bot and load extensions"""
        # Load environment variables
        load_dotenv()

        # Validate required environment variables
        required_vars = ['BOT_TOKEN', 'GITHUB_TOKEN']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

        # Load extensions
        await self.extension_manager.load_all()

        # Start web server
        keep_alive()

    async def start(self):
        """Start the bot"""
        try:
            await self.setup()
            await self.bot.start(os.getenv('BOT_TOKEN'))
        except Exception as e:
            logging.error(f"❌ Failed to start bot: {str(e)}")
            raise

# Initialize bot manager
bot_manager = BotManager(bot, extension_manager)

# Main function
async def main():
    try:
        await bot_manager.start()
    except Exception as e:
        logging.critical(f"❌ Critical error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())

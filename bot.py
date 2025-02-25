import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
import logging
from dotenv import load_dotenv
import time
import base64
import requests
from myserver import keep_alive  # Import keep_alive function

config = {
    "prefix": "!"
}

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ตั้งค่า Intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config["prefix"], intents=intents)
bot.config = config
start_time = time.time()

# คำนวณเวลา uptime
def get_uptime():
    s = int(time.time() - start_time)
    return f"{s//3600}h {(s%3600)//60}m {s%60}s"

# อัปเดตสถานะบอท
@tasks.loop(seconds=5)
async def update_presence():
    await bot.change_presence(activity=discord.Game(name=f"Online for {get_uptime()}"))

bot.update_presence = update_presence

# โหลดค่าการตั้งค่าของเซิร์ฟเวอร์
def get_server_config(guild_id):
    path = f"configs/{guild_id}.json"
    if os.path.exists(path):
        try:
            with open(path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            logging.error(f"❌ อ่านไฟล์ {guild_id}.json ไม่ได้")
    return {"notify_channel_id": None}

# จัดการการตั้งค่าเซิร์ฟเวอร์
def save_server_config(guild_id, server_config):
    # บันทึกลง GitHub
    url = f"https://api.github.com/repos/fomm1802/Bot/contents/configs/{guild_id}.json"
    headers = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"}
    response = requests.get(url, headers=headers)
    data = {
        "message": f"Update config for guild {guild_id}",
        "content": base64.b64encode(json.dumps(server_config, indent=4).encode()).decode(),
        "branch": "main",
        "sha": response.json().get('sha') if response.status_code == 200 else None
    }
    res = requests.put(url, headers=headers, json=data)
    logging.info(f"✅ อัปเดตไฟล์สำเร็จ" if res.status_code in (200, 201) else f"❌ อัปเดตล้มเหลว {res.text}")

    # บันทึกลงไฟล์
    path = f"configs/{guild_id}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as file:
        json.dump(server_config, file, indent=4)

# โหลด Extensions อัตโนมัติจากโฟลเดอร์ events/ และ commands/
async def load_extensions():
    for folder in ["events", "commands"]:
        for file in os.listdir(folder):
            if file.endswith(".py"):
                ext = f"{folder}.{file[:-3]}"
                try:
                    await bot.load_extension(ext)
                    logging.info(f"✅ โหลด {ext} สำเร็จ!")
                except Exception as e:
                    logging.error(f"❌ โหลด {ext} ล้มเหลว: {e}")

# ฟังก์ชันหลัก
async def main():
    load_dotenv()
    keep_alive()  # Start the Flask server
    await load_extensions()
    await bot.start(os.getenv("BOT_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())
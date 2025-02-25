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

# โหลดการตั้งค่าจากไฟล์ config.json
def load_config():
    try:
        with open("config.json", "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError):
        raise Exception("ไฟล์ config.json หายไปหรือมีข้อผิดพลาดในการอ่านข้อมูล")

config = load_config()

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

# ตั้งค่า Intents
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=config["prefix"], intents=intents)
bot.config = config
start_time = time.time()

# คำนวณเวลา uptime
def get_uptime():
    uptime_seconds = int(time.time() - start_time)
    return f"{uptime_seconds // 3600}h {(uptime_seconds % 3600) // 60}m {uptime_seconds % 60}s"

# อัปเดตสถานะบอท
@tasks.loop(seconds=5)
async def update_presence():
    await bot.change_presence(activity=discord.Game(name=f"Online for {get_uptime()}"))

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

# ตรวจสอบไฟล์ใน GitHub
def check_if_file_exists_on_github(guild_id):
    url = f"https://api.github.com/repos/fomm1802/Bot/contents/configs/{guild_id}.json"
    headers = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"}
    return requests.get(url, headers=headers).status_code == 200

# บันทึกการตั้งค่าของเซิร์ฟเวอร์ลง GitHub
def save_server_config_to_github(guild_id, server_config):
    url = f"https://api.github.com/repos/fomm1802/Bot/contents/configs/{guild_id}.json"
    headers = {"Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}"}
    response = requests.get(url, headers=headers)
    sha = response.json().get('sha') if response.status_code == 200 else None
    data = {
        "message": f"Update config for guild {guild_id}",
        "content": base64.b64encode(json.dumps(server_config, indent=4).encode()).decode(),
        "branch": "main",
        "sha": sha
    }
    res = requests.put(url, headers=headers, json=data)
    logging.info(f"✅ อัปเดตไฟล์สำเร็จ" if res.status_code in (200, 201) else f"❌ อัปเดตล้มเหลว {res.text}")

# บันทึกการตั้งค่าของเซิร์ฟเวอร์
def save_server_config(guild_id, server_config):
    save_server_config_to_github(guild_id, server_config)
    path = f"configs/{guild_id}.json"
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as file:
        json.dump(server_config, file, indent=4)

# ตั้งค่าช่องแจ้งเตือน
@bot.command(name='set_notify_channel')
@commands.has_permissions(administrator=True)
async def set_notify_channel(ctx):
    guild_id, channel_id = ctx.guild.id, ctx.channel.id
    server_config = get_server_config(guild_id)
    if check_if_file_exists_on_github(guild_id):
        logging.info(f"✅ พบไฟล์ {guild_id}.json ใน GitHub")
    else:
        logging.info(f"ℹ️ ไม่มีไฟล์ {guild_id}.json จะสร้างใหม่")
    
    if server_config['notify_channel_id'] == channel_id:
        return await ctx.send(f"🔔 ช่องแจ้งเตือนนี้ถูกตั้งค่าแล้ว: <#{channel_id}>")
    
    server_config['notify_channel_id'] = channel_id
    save_server_config(guild_id, server_config)
    await ctx.send(f"🔔 ช่องแจ้งเตือนถูกตั้งค่าเป็น: <#{channel_id}>")

# โหลด Extensions อัตโนมัติจากโฟลเดอร์ events/
async def load_extensions():
    # โหลด Events
    events_path = "events"
    for filename in os.listdir(events_path):
        if filename.endswith(".py"):
            ext = f"events.{filename[:-3]}"
            try:
                await bot.load_extension(ext)
                logging.info(f"✅ โหลด {ext} สำเร็จ!")
            except Exception as e:
                logging.error(f"❌ โหลด {ext} ล้มเหลว: {e}")

    # โหลด Commands
    commands_path = "commands"
    for filename in os.listdir(commands_path):
        if filename.endswith(".py"):
            ext = f"commands.{filename[:-3]}"
            try:
                await bot.load_extension(ext)
                logging.info(f"✅ โหลด {ext} สำเร็จ!")
            except Exception as e:
                logging.error(f"❌ โหลด {ext} ล้มเหลว: {e}")

@bot.event
async def on_ready():
    logging.info(f"Bot is online as {bot.user}")
    update_presence.start()

# ฟังก์ชันหลัก
async def main():
    load_dotenv()
    await load_extensions()
    await bot.start(os.getenv("BOT_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())

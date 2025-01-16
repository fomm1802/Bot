import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
import logging
from dotenv import load_dotenv
import time
from myserver import keep_alive
import base64
import requests

# ฟังก์ชันในการโหลดการตั้งค่าจากไฟล์ config.json
def load_config():
    try:
        with open("config.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise Exception("ไม่พบไฟล์ config.json")
    except json.JSONDecodeError:
        raise Exception("ไฟล์ config.json มีข้อผิดพลาดในการอ่านข้อมูล")

config = load_config()

# การตั้งค่าสีสำหรับข้อความ Log
LOG_COLORS = {
    'DEBUG': '\033[94m',
    'INFO': '\033[92m',
    'WARNING': '\033[93m',
    'ERROR': '\033[91m',
    'CRITICAL': '\033[95m'
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        log_color = LOG_COLORS.get(record.levelname, '\033[0m')
        reset_color = '\033[0m'
        record.levelname = f"{log_color}{record.levelname}{reset_color}"
        return super().format(record)

logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(message)s')
for handler in logging.root.handlers:
    handler.setFormatter(ColoredFormatter('%(levelname)s:%(message)s'))

# การตั้งค่า Intents สำหรับ Discord
intents = discord.Intents.all()
intents.members = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix=config["prefix"], intents=intents)
bot.config = config

# Track the bot's start time
start_time = time.time()

# ฟังก์ชันในการคำนวณเวลาที่บอทออนไลน์
def get_uptime():
    uptime_seconds = int(time.time() - start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    return f"{hours}h {minutes}m {seconds}s"

# อัปเดตสถานะของบอทเป็นเวลาออนไลน์
@tasks.loop(seconds=5)  # อัปเดตทุกๆ 5 วินาที
async def update_presence():
    uptime = get_uptime()
    await bot.change_presence(activity=discord.Game(name=f"Online for {uptime}"))

# ฟังก์ชันการโหลดและบันทึกการตั้งค่าของเซิร์ฟเวอร์
def get_server_config(guild_id):
    server_config_path = f"configs/{guild_id}.json"
    if os.path.exists(server_config_path):
        try:
            with open(server_config_path, "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            logging.error(f"❌ ไม่สามารถอ่านไฟล์การตั้งค่าของเซิร์ฟเวอร์ {guild_id}. ใช้ค่าดีฟอลต์แทน")
            return {"notify_channel_id": None}
    else:
        logging.info(f"ℹ️ ไม่มีไฟล์การตั้งค่าสำหรับเซิร์ฟเวอร์ {guild_id}. ใช้ค่าดีฟอลต์แทน")
        return {"notify_channel_id": None}

# ฟังก์ชันในการตรวจสอบว่าไฟล์การตั้งค่าเซิร์ฟเวอร์มีอยู่ใน GitHub หรือไม่
def check_if_file_exists_on_github(guild_id):
    repo_owner = "fomm1802"  # ชื่อเจ้าของ repository
    repo_name = "Bot"  # ชื่อ repository
    file_path = f"configs/{guild_id}.json"  # ที่อยู่ไฟล์ใน repository
    github_token = os.getenv("GITHUB_TOKEN")  # ดึง GITHUB_TOKEN จาก .env
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    
    # ส่งคำขอ GET ไปยัง GitHub API เพื่อตรวจสอบว่าไฟล์มีอยู่หรือไม่
    response = requests.get(url, headers={"Authorization": f"Bearer {github_token}"})
    
    if response.status_code == 200:
        return True  # หากได้รับการตอบกลับด้วย status 200 แสดงว่าไฟล์มีอยู่
    else:
        return False  # หากไม่พบไฟล์

# ฟังก์ชันการบันทึกการตั้งค่าของเซิร์ฟเวอร์ไปยัง GitHub
def save_server_config_to_github(guild_id, server_config):
    repo_owner = "fomm1802"  # ชื่อเจ้าของ repository
    repo_name = "Bot"  # ชื่อ repository
    file_path = f"configs/{guild_id}.json"  # ที่อยู่ไฟล์ใน repository
    github_token = os.getenv("GITHUB_TOKEN")  # ดึง GITHUB_TOKEN จาก .env
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file_path}"
    
    # ดึงข้อมูลไฟล์จาก GitHub ถ้ามีอยู่
    response = requests.get(url, headers={"Authorization": f"Bearer {github_token}"})
    if response.status_code == 200:
        file_info = response.json()
        sha = file_info['sha']  # SHA ของไฟล์ใน GitHub
    else:
        sha = None  # ถ้าไม่มีไฟล์ ให้สร้างไฟล์ใหม่
    
    # เข้ารหัสเนื้อหาการตั้งค่าเป็น Base64
    encoded_content = base64.b64encode(json.dumps(server_config, indent=4).encode()).decode()
    
    # ข้อมูลที่จะส่งไปยัง GitHub
    data = {
        "message": f"Update config for guild {guild_id}",
        "content": encoded_content,
        "branch": "main",  # ใช้ branch ที่ต้องการ
    }
    if sha:
        data["sha"] = sha  # ถ้ามีไฟล์อยู่แล้ว จะใช้ SHA ในการอัปเดต
    
    # ส่งคำขอ PUT ไปยัง GitHub API
    response = requests.put(url, headers={"Authorization": f"Bearer {github_token}"}, json=data)
    
    if response.status_code in (200, 201):
        logging.info(f"✅ อัปเดตไฟล์ {file_path} สำเร็จใน GitHub!")
    else:
        logging.error(f"❌ ไม่สามารถอัปเดตไฟล์ {file_path} ใน GitHub: {response.status_code} {response.text}")

# ฟังก์ชันในการบันทึกการตั้งค่าของเซิร์ฟเวอร์
def save_server_config(guild_id, server_config):
    save_server_config_to_github(guild_id, server_config)  # อัปเดตไฟล์ใน GitHub
    # ถ้าคุณต้องการบันทึกลงไฟล์ในเครื่อง ให้ใช้โค้ดนี้
    server_config_path = f"configs/{guild_id}.json"
    os.makedirs(os.path.dirname(server_config_path), exist_ok=True)
    with open(server_config_path, "w") as file:
        json.dump(server_config, file, indent=4)

# ฟังก์ชันการตั้งค่าช่องแจ้งเตือน
@bot.command(name='set_notify_channel')
@commands.has_permissions(administrator=True)
async def set_notify_channel(ctx):
    guild_id = ctx.guild.id
    server_config = get_server_config(guild_id)
    
    # เช็คว่าไฟล์การตั้งค่ามีอยู่ใน GitHub หรือไม่
    if check_if_file_exists_on_github(guild_id):
        logging.info(f"✅ พบไฟล์การตั้งค่า {guild_id}.json อยู่ใน GitHub")
    else:
        logging.info(f"ℹ️ ไม่พบไฟล์การตั้งค่า {guild_id}.json ใน GitHub จะสร้างไฟล์ใหม่")
    
    # ดึง ID ของห้องที่ส่งคำสั่ง
    channel_id = ctx.channel.id
    
    # เช็คว่าช่องแจ้งเตือนถูกตั้งค่าหรือยัง
    if server_config['notify_channel_id'] == channel_id:
        await ctx.send(f"🔔 ช่องแจ้งเตือนนี้ถูกตั้งค่าแล้ว: <#{channel_id}>")
        return  # ไม่ทำการบันทึกซ้ำ

    # อัปเดตการตั้งค่า
    server_config['notify_channel_id'] = channel_id
    save_server_config(guild_id, server_config)  # บันทึกการตั้งค่าไปยัง GitHub และเครื่อง
    
    await ctx.send(f"🔔 ช่องแจ้งเตือนถูกตั้งค่าเป็น: <#{channel_id}> สำหรับเซิร์ฟเวอร์นี้เรียบร้อยแล้ว!")

# รายการ Extension ที่จะโหลด
initial_extensions = [
    "events.voice_events",
]

os.system('clear')

logo = """
 GGGGG    U   U   RRRR    AAAAA      BBBB     OOO    TTTTT
G         U   U   R   R  A     A     B   B   O   O     T
G  GG     U   U   RRRR   AAAAAAA     BBBBB   O   O     T
G   G     U   U   R  R   A     A     B   B   O   O     T
 GGGG      UUU    R   R  A     A     BBBB     OOO      T
"""

# Print the logo
print(logo)

# ฟังก์ชันหลักในการเริ่มบอท
async def main():
    logging.info("📦 กำลังโหลด Extensions...")
    for extension in initial_extensions:
        try:
            await bot.load_extension(extension)
            logging.info(f"✅ โหลด {extension} สำเร็จ!")
        except Exception as e:
            logging.error(f"❌ ไม่สามารถโหลด {extension}: {e}")

    logging.info("🚀 เริ่มบอท...")
    try:
        os.environ["BOT_STATUS"] = "running"
        await bot.start(os.getenv("BOT_TOKEN"))
    except discord.errors.LoginFailure:
        logging.critical("ไม่สามารถเริ่มบอทได้: Improper token has been passed.")
    except Exception as e:
        logging.critical(f"ไม่สามารถเริ่มบอทได้: {e}")
    finally:
        os.environ["BOT_STATUS"] = "not running"

@bot.event
async def on_ready():
    logging.info(f"Bot is online and ready! Logged in as {bot.user}")
    update_presence.start()  # เริ่มต้นการอัปเดตสถานะ

if __name__ == "__main__":
    load_dotenv()  # Load environment variables from .env file
    keep_alive()  # เริ่มให้เซิร์ฟเวอร์อยู่บนไลน์
    asyncio.run(main())

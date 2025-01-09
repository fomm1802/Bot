import discord
from discord.ext import commands, tasks
import asyncio
import json
import os
import logging
from firebase_admin import credentials, initialize_app, firestore
from dotenv import load_dotenv
import time

# Firebase Initialization
cred = credentials.Certificate("serviceAccountKey.json")
firebase_app = initialize_app(cred)
db = firestore.client()

# ฟังก์ชันในการโหลด config.json
def load_config():
    try:
        with open("config.json", "r") as file:
            config = json.load(file)
            required_keys = ["prefix", "BOT_TOKEN"]
            for key in required_keys:
                if key not in config:
                    raise Exception(f"Missing required key: {key}")
            return config
    except FileNotFoundError:
        raise Exception("ไม่พบไฟล์ config.json")
    except json.JSONDecodeError:
        raise Exception("ไฟล์ config.json มีข้อผิดพลาดในการอ่านข้อมูล")

config = load_config()

# การตั้งค่า Logging
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

# การตั้งค่า Intents
intents = discord.Intents.all()
intents.members = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix=config["prefix"], intents=intents)
bot.config = config

# Track the bot's start time
start_time = time.time()

# ฟังก์ชันคำนวณ Uptime
def get_uptime():
    uptime_seconds = int(time.time() - start_time)
    hours = uptime_seconds // 3600
    minutes = (uptime_seconds % 3600) // 60
    seconds = uptime_seconds % 60
    return f"{hours}h {minutes}m {seconds}s"

# ฟังก์ชันในการตั้งค่าช่องแจ้งเตือนและบันทึกลง Firebase
@bot.command(name='set_notify_channel')
@commands.has_permissions(administrator=True)
async def set_notify_channel(ctx):
    guild_id = str(ctx.guild.id)
    channel_id = str(ctx.channel.id)

    # บันทึกข้อมูลลง Firebase
    db.collection("server_configs").document(guild_id).set({
        "notify_channel_id": channel_id
    })

    await ctx.send(f"🔔 ตั้งค่าช่องแจ้งเตือนเป็น: <#{channel_id}> สำเร็จ!")

# ฟังก์ชันดึงข้อมูลการตั้งค่าจาก Firebase
def get_server_config(guild_id):
    try:
        doc = db.collection("server_configs").document(str(guild_id)).get()
        if doc.exists:
            return doc.to_dict()
        else:
            return {"notify_channel_id": None}
    except Exception as e:
        logging.error(f"ไม่สามารถโหลดการตั้งค่าสำหรับเซิร์ฟเวอร์ {guild_id}: {e}")
        return {"notify_channel_id": None}

# อัปเดตสถานะบอท
@tasks.loop(seconds=10)
async def update_presence():
    uptime = get_uptime()
    guild_count = len(bot.guilds)
    await bot.change_presence(activity=discord.Game(name=f"Online: {uptime} | Servers: {guild_count}"))

# คำสั่งแสดงสถานะบอท
@bot.command(name="status")
async def status(ctx):
    uptime = get_uptime()
    guild_count = len(bot.guilds)
    await ctx.send(f"✅ Bot is online!\n- Uptime: {uptime}\n- Connected Servers: {guild_count}")

# โหลด Extensions
initial_extensions = []

os.system('clear')

logo = """
 GGGGG    U   U   RRRR    AAAAA      BBBB     OOO    TTTTT
G         U   U   R   R  A     A     B   B   O   O     T
G  GG     U   U   RRRR   AAAAAAA     BBBBB   O   O     T
G   G     U   U   R  R   A     A     B   B   O   O     T
 GGGG      UUU    R   R  A     A     BBBB     OOO      T
"""

print(logo)

# Event เมื่อบอทพร้อมใช้งาน
@bot.event
async def on_ready():
    logging.info(f"Bot is online and ready! Logged in as {bot.user}")
    update_presence.start()

# ฟังก์ชันเริ่มต้นบอท
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
        await bot.start(os.getenv("BOT_TOKEN"))
    except discord.errors.LoginFailure:
        logging.critical("ไม่สามารถเริ่มบอทได้: Improper token has been passed.")
    except Exception as e:
        logging.critical(f"ไม่สามารถเริ่มบอทได้: {e}")

if __name__ == "__main__":
    load_dotenv()
    asyncio.run(main())

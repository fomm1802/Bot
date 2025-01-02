import discord
from discord.ext import commands
import asyncio
import json
import os
import logging
from myserver import keep_alive
from dotenv import load_dotenv

load_dotenv()

def load_config():
    try:
        with open("config.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        raise Exception("ไม่พบไฟล์ config.json")
    except json.JSONDecodeError:
        raise Exception("ไฟล์ config.json มีข้อผิดพลาดในการอ่านข้อมูล")

config = load_config()

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

intents = discord.Intents.all()
intents.members = True
intents.voice_states = True
intents.guilds = True

bot = commands.Bot(command_prefix=config["prefix"], intents=intents)
bot.config = config

@bot.command(name='set_notify_channel')
@commands.has_permissions(administrator=True)
async def set_notify_channel(ctx, channel_id: int):
    bot.config['notify_channel_id'] = channel_id
    with open('config.json', 'w') as file:
        json.dump(bot.config, file, indent=4)
    os.environ["NOTIFY_CHANNEL_ID"] = str(channel_id)
    await ctx.send(f"🔔 เปลี่ยนช่องแจ้งเตือนเป็น <#{channel_id}> เรียบร้อยแล้ว")

initial_extensions = [
    "events.voice_events",
]

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
        os.environ["NOTIFY_CHANNEL_ID"] = str(config["notify_channel_id"])
        await bot.start(os.getenv("BOT_TOKEN"))
    except discord.errors.LoginFailure:
        logging.critical("ไม่สามารถเริ่มบอทได้: Improper token has been passed.")
    except Exception as e:
        logging.critical(f"ไม่สามารถเริ่มบอทได้: {e}")
    finally:
        os.environ["BOT_STATUS"] = "not running"

if __name__ == "__main__":
    keep_alive()
    asyncio.run(main())

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
from myserver import keep_alive

config = {
    "prefix": "!"
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

intents = discord.Intents.all()

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.start_time = time.time()

    async def setup_hook(self):
        self.update_presence_task = self.loop.create_task(self.update_presence())
        await self.load_extensions()
        logging.info(f"✅ Bot is online as {self.user}")  # ย้าย log มาที่นี่

    def get_uptime(self):
        s = int(time.time() - self.start_time)
        return f"{s//3600}h {(s%3600)//60}m {s%60}s"

    async def update_presence(self):
        await self.wait_until_ready()
        while not self.is_closed():
            await self.change_presence(activity=discord.Game(name=f"Online for {self.get_uptime()}"))
            await asyncio.sleep(5)

    async def load_extensions(self):
        for folder in ["events", "commands"]:
            for file in os.listdir(folder):
                if file.endswith(".py"):
                    ext = f"{folder}.{file[:-3]}"
                    try:
                        await self.load_extension(ext)
                        logging.info(f"✅ โหลด {ext} สำเร็จ!")
                    except Exception as e:
                        logging.error(f"❌ โหลด {ext} ล้มเหลว: {e}")

async def main():
    load_dotenv()
    keep_alive()
    bot = MyBot(command_prefix=config["prefix"], intents=intents)
    await bot.start(os.getenv("BOT_TOKEN"))

if __name__ == "__main__":
    asyncio.run(main())

import discord
from discord.ext import commands
import asyncio
import json
import os
import logging
from dotenv import load_dotenv
import time
from myserver import keep_alive

# ตั้งค่าพื้นฐาน
config = {
    "prefix": "!"
}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# เปิด Intent ที่จำเป็น
intents = discord.Intents.default()
intents.message_content = True  # เปิด Intent สำหรับเนื้อหาข้อความ

class MyBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.start_time = time.time()

    async def setup_hook(self):
        """ รันโค้ดที่ต้องใช้ก่อนที่บอทจะเริ่มทำงาน """
        self.update_presence_task = self.loop.create_task(self.update_presence())
        await self.load_extensions()
        logging.info(f"✅ Bot is online as {self.user}")  # Log แสดงสถานะบอท

    def get_uptime(self):
        """ คืนค่าเวลาที่บอทออนไลน์อยู่ """
        s = int(time.time() - self.start_time)
        return f"{s//3600}h {(s%3600)//60}m {s%60}s"

    async def update_presence(self):
        """ อัปเดตสถานะของบอททุก ๆ 5 วินาที """
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                await self.change_presence(activity=discord.Game(name=f"Online for {self.get_uptime()}"))
                await asyncio.sleep(5)
            except Exception as e:
                logging.error(f"Error updating presence: {e}")

    async def load_extensions(self):
        """ โหลดไฟล์ในโฟลเดอร์ `events/` และ `commands/` อัตโนมัติ """
        for folder in ["events", "commands"]:
            if os.path.exists(folder):  # ตรวจสอบว่าโฟลเดอร์มีอยู่จริง
                for file in os.listdir(folder):
                    if file.endswith(".py"):
                        ext = f"{folder}.{file[:-3]}"
                        try:
                            await self.load_extension(ext)
                            logging.info(f"✅ โหลด {ext} สำเร็จ!")
                        except Exception as e:
                            logging.error(f"❌ โหลด {ext} ล้มเหลว: {e}")

async def main():
    """ ฟังก์ชันหลักของบอท """
    load_dotenv()  # โหลดตัวแปรจาก .env
    TOKEN = os.getenv("BOT_TOKEN")

    if not TOKEN:
        logging.error("❌ BOT_TOKEN ไม่พบใน .env")
        return

    keep_alive()  # เปิด Flask server ถ้ามีใช้งาน
    bot = MyBot(command_prefix=config["prefix"], intents=intents)
    await bot.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())

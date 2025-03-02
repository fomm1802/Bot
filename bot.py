import discord
from discord.ext import commands
import asyncio
import os
import logging
from dotenv import load_dotenv
import time

config = {"prefix": "!"}

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

intents = discord.Intents.default()
intents.message_content = True


class MyBot(commands.AutoShardedBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.config = config
        self.start_time = time.time()

    async def setup_hook(self):
        self.update_presence_task = self.loop.create_task(self.update_presence())
        await self.load_extensions()  # Move the load_extensions call here
        logging.info(f"✅ Node 2 Online as {self.user}")

    def get_uptime(self):
        s = int(time.time() - self.start_time)
        return f"{s//3600}h {(s%3600)//60}m {s%60}s"

    # Move update_presence to be inside MyBot class
    async def update_presence(self):
        await self.wait_until_ready()  # รอให้บอทพร้อมทำงาน

        # สร้าง task เพื่อให้ทั้งสอง Node อัปเดตสถานะแยกกัน
        task_node_1 = asyncio.create_task(self.update_node_1_presence())
        task_node_2 = asyncio.create_task(self.update_node_2_presence())

        # รอให้ task ทั้งสองทำงาน
        await asyncio.gather(task_node_1, task_node_2)

    async def update_node_1_presence(self):
        while not self.is_closed():  # เช็คว่าบอทยังไม่ปิดการเชื่อมต่อ
            try:
                # แสดงสถานะของ Node 1 (ออนไลน์)
                activity_text_node_1 = f"Node 1: Online"
                # เปลี่ยนสถานะการแสดงผลของบอทสำหรับ Node 1
                await self.change_presence(
                    activity=discord.Game(name=activity_text_node_1)
                )
                await asyncio.sleep(5)  # รอ 5 วินาที
            except Exception as e:
                logging.error(f"Error updating Node 1 presence: {e}")

    async def update_node_2_presence(self):
        while not self.is_closed():  # เช็คว่าบอทยังไม่ปิดการเชื่อมต่อ
            try:
                # แสดงสถานะของ Node 2 (ออนไลน์)
                activity_text_node_2 = f"Node 2: Online"
                # เปลี่ยนสถานะการแสดงผลของบอทสำหรับ Node 2
                await self.change_presence(
                    activity=discord.Game(name=activity_text_node_2)
                )
                await asyncio.sleep(5)  # รอ 5 วินาที
            except Exception as e:
                logging.error(f"Error updating Node 2 presence: {e}")

    async def load_extensions(self):
        for folder in ["events", "commands"]:
            if os.path.exists(folder):
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
    TOKEN = os.getenv("BOT_TOKEN")

    if not TOKEN:
        logging.error("❌ BOT_TOKEN ไม่พบใน .env")
        return

    bot = MyBot(
        command_prefix=config["prefix"], intents=intents, shard_ids=[1], shard_count=2
    )  # Node 1 ดูแลเฉพาะ Shard 0
    await bot.start(TOKEN)


if __name__ == "__main__":
    asyncio.run(main())

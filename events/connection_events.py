import discord
from discord.ext import commands
import logging
import asyncio
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class Events(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = None
        self.status_task = None

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.start_time:
            self.start_time = datetime.now()
            logging.info(f"✅ บอทพร้อมใช้งาน! เข้าสู่ระบบในชื่อ {self.bot.user}")
            
            if not self.status_task:
                self.status_task = self.bot.loop.create_task(self.update_status())

    @commands.Cog.listener()
    async def on_disconnect():
        logging.warning("⚠️ บอทหลุดการเชื่อมต่อ!")

    @commands.Cog.listener()
    async def on_resumed():
        logging.info("✅ บอทกลับมาเชื่อมต่อแล้ว!")

    async def update_status(self):
        while not self.bot.is_closed():
            try:
                uptime = datetime.now() - self.start_time
                hours = uptime.total_seconds() // 3600
                
                await self.bot.change_presence(
                    activity=discord.Activity(
                        type=discord.ActivityType.watching,
                        name=f"🟢 ออนไลน์ {int(hours)} ชั่วโมง"
                    )
                )
            except Exception as e:
                logging.error(f"❌ ไม่สามารถอัพเดทสถานะได้: {e}")
            await asyncio.sleep(60)  # อัพเดททุก 1 นาที

async def setup(bot):
    await bot.add_cog(Events(bot))

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
        self.ready_once = False
        self.last_status_update = None

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.ready_once:
            self.ready_once = True
            self.start_time = datetime.now()
            logging.info(f"✅ บอทพร้อมใช้งาน! | {self.bot.user}")
            
            if not self.status_task or self.status_task.done():
                self.status_task = self.bot.loop.create_task(self.update_status())

    async def update_status(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                current_time = datetime.now()
                # อัพเดทสถานะทุก 5 นาที
                if not self.last_status_update or (current_time - self.last_status_update).total_seconds() >= 300:
                    uptime = current_time - self.start_time
                    hours = uptime.total_seconds() // 3600
                    await self.bot.change_presence(
                        activity=discord.Activity(
                            type=discord.ActivityType.watching,
                            name=f"🟢 ออนไลน์ {int(hours)} ชั่วโมง"
                        ),
                        status=discord.Status.online
                    )
                    self.last_status_update = current_time
            except Exception as e:
                logging.error(f"❌ ไม่สามารถอัพเดทสถานะ: {e}")
            await asyncio.sleep(60)

async def setup(bot):
    await bot.add_cog(Events(bot))

import logging
import asyncio
import os
from discord.ext import commands

class ConnectionEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        os.environ["BOT_STATUS"] = "running"
        logging.info(f"Bot is online as {self.bot.user}")
        if not self.bot.update_presence.is_running():
            self.bot.update_presence.start()

    @commands.Cog.listener()
    async def on_disconnect(self):
        os.environ["BOT_STATUS"] = "not_running"
        logging.warning("Bot disconnected! Attempting to reconnect...")
        await self.retry_connect()

    async def retry_connect(self):
        retry_delay = 5
        max_retries = 5
        for attempt in range(max_retries):
            try:
                await self.bot.close()
                await self.bot.start(os.getenv("BOT_TOKEN"))
                os.environ["BOT_STATUS"] = "running"
                logging.info("Reconnected successfully!")
                return
            except Exception as e:
                logging.error(f"Reconnect attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2

async def setup(bot):
    await bot.add_cog(ConnectionEvents(bot))

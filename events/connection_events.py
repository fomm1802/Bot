import logging
import asyncio
from discord.ext import commands

class ConnectionEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_disconnect(self):
        logging.warning("Bot disconnected! Attempting to reconnect...")
        await self.retry_connect()

    async def retry_connect(self):
        retry_delay = 5  # Initial delay in seconds
        max_retries = 5  # Maximum number of retries
        for attempt in range(max_retries):
            try:
                await self.bot.connect(reconnect=True)
                logging.info("Reconnected successfully!")
                return
            except Exception as e:
                logging.error(f"Reconnect attempt {attempt + 1} failed: {e}")
                await asyncio.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

async def setup(bot):
    await bot.add_cog(ConnectionEvents(bot))

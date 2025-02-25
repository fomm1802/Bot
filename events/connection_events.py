import logging
import asyncio
import os
from discord.ext import commands

async def on_ready(bot):
    os.environ["BOT_STATUS"] = "running"
    logging.info(f"Bot is online as {bot.user}")
    if not bot.update_presence.is_running():
        bot.update_presence.start()

async def on_disconnect(bot):
    os.environ["BOT_STATUS"] = "not_running"
    logging.warning("Bot disconnected! Attempting to reconnect...")
    await retry_connect(bot)

async def retry_connect(bot):
    retry_delay = 5
    max_retries = 10
    for attempt in range(max_retries):
        try:
            await bot.close()
            await bot.start(os.getenv("BOT_TOKEN"))
            os.environ["BOT_STATUS"] = "running"
            logging.info("Reconnected successfully!")
            return
        except Exception as e:
            logging.error(f"Reconnect attempt {attempt + 1} failed: {e}")
            await asyncio.sleep(retry_delay)
            retry_delay = min(retry_delay * 2, 300)  # Cap the delay at 5 minutes

async def setup(bot):
    bot.add_listener(on_ready, 'on_ready')
    bot.add_listener(on_disconnect, 'on_disconnect')

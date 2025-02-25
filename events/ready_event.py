from discord.ext import commands, tasks
import logging

async def on_ready(bot):
    logging.info(f"Bot is online as {bot.user}")
    if not bot.update_presence.is_running():
        bot.update_presence.start()

async def setup(bot):
    bot.add_listener(on_ready, 'on_ready')
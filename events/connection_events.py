import discord
from discord.ext import commands
import logging

async def setup(bot):
    @bot.event
    async def on_connect():
        logging.info("✅ Bot connected to Discord!")

    @bot.event
    async def on_disconnect():
        logging.warning("⚠️ Bot disconnected from Discord!")

    @bot.event
    async def on_resumed():
        logging.info("✅ Bot connection resumed!")
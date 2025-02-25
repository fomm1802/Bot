from discord.ext import commands, tasks
import logging

class ReadyEvent(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        logging.info(f"Bot is online as {self.bot.user}")
        if not self.bot.update_presence.is_running():
            self.bot.update_presence.start()

async def setup(bot):
    await bot.add_cog(ReadyEvent(bot))

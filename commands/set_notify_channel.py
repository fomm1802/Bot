from discord.ext import commands
import logging
from bot import ServerConfig

class SetNotifyChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='set_notify_channel')
    @commands.has_permissions(administrator=True)
    async def set_notify_channel(self, ctx):
        guild_id, channel_id = str(ctx.guild.id), ctx.channel.id
        server_config = ServerConfig(guild_id)

        exists = await server_config.exists_on_github()
        if exists:
            logging.info(f"✅ พบไฟล์ {guild_id}.json ใน GitHub")
        else:
            logging.info(f"ℹ️ ไม่มีไฟล์ {guild_id}.json จะสร้างใหม่")

        current_channel = server_config.get('notify_channel_id')
        if current_channel == channel_id:
            return await ctx.send(f"🔔 ช่องแจ้งเตือนนี้ถูกตั้งค่าแล้ว: <#{channel_id}>")

        server_config.set('notify_channel_id', channel_id)
        await server_config.save()
        await ctx.send(f"🔔 ช่องแจ้งเตือนถูกตั้งค่าเป็น: <#{channel_id}>")

async def setup(bot):
    await bot.add_cog(SetNotifyChannel(bot))
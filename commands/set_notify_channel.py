from discord.ext import commands
import logging
from bot import get_server_config, save_server_config, check_if_file_exists_on_github

@commands.command(name='set_notify_channel')
@commands.has_permissions(administrator=True)
async def set_notify_channel(ctx):
    guild_id, channel_id = ctx.guild.id, ctx.channel.id
    server_config = get_server_config(guild_id)
    if check_if_file_exists_on_github(guild_id):
        logging.info(f"✅ พบไฟล์ {guild_id}.json ใน GitHub")
    else:
        logging.info(f"ℹ️ ไม่มีไฟล์ {guild_id}.json จะสร้างใหม่")
    
    if server_config['notify_channel_id'] == channel_id:
        return await ctx.send(f"🔔 ช่องแจ้งเตือนนี้ถูกตั้งค่าแล้ว: <#{channel_id}>")
    
    server_config['notify_channel_id'] = channel_id
    save_server_config(guild_id, server_config)
    await ctx.send(f"🔔 ช่องแจ้งเตือนถูกตั้งค่าเป็น: <#{channel_id}>")

async def setup(bot):
    bot.add_command(set_notify_channel)

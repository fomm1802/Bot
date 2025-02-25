import discord
from discord.ext import commands
import logging
import asyncio
from datetime import datetime
from utils import get_server_config

async def on_voice_state_update(member, before, after):
    if member.bot:
        return

    server_config = get_server_config(member.guild.id)
    notify_channel_id = server_config.get("notify_channel_id")

    if not notify_channel_id:
        logging.warning(f"⚠️ เซิร์ฟเวอร์ {member.guild.id} ยังไม่ได้ตั้งค่าช่องแจ้งเตือน")
        return

    channel = member.guild.get_channel(notify_channel_id)
    if not channel:
        logging.warning(f"⚠️ ไม่พบช่องแจ้งเตือนในเซิร์ฟเวอร์ {member.guild.id}")
        return

    def create_embed(event_type, member, before_channel=None, after_channel=None):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        embed = discord.Embed(timestamp=datetime.now(), color=discord.Color.blue())
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)
        if event_type == "join":
            embed.title = "🔊 เข้าช่องเสียง"
            embed.description = f"**{member.display_name}** เข้าช่องเสียง: `{after_channel}`"
        elif event_type == "leave":
            embed.title = "🔇 ออกจากช่องเสียง"
            embed.description = f"**{member.display_name}** ออกจากช่องเสียง: `{before_channel}`"
        elif event_type == "move":
            embed.title = "🔀 ย้ายช่องเสียง"
            embed.description = f"**{member.display_name}** ย้ายจาก `{before_channel}` ไปยัง `{after_channel}`"
        embed.set_footer(text=f"เวลา {now}")
        return embed

    if before.channel is None and after.channel is not None:
        if after.channel.name == "Join Here":
            await asyncio.sleep(1)
            after = member.voice
            after_channel_name = after.channel.name if after and after.channel else None
            if after_channel_name:
                await channel.send(embed=create_embed("join", member, after_channel=after_channel_name))
            return
        await channel.send(embed=create_embed("join", member, after_channel=after.channel.name))
    elif before.channel is not None and after.channel is None:
        await channel.send(embed=create_embed("leave", member, before_channel=before.channel.name))
    elif before.channel != after.channel:
        if before.channel.name == "Join Here":
            return
        await channel.send(embed=create_embed("move", member, before_channel=before.channel.name, after_channel=after.channel.name))

async def setup(bot):
    bot.add_listener(on_voice_state_update, 'on_voice_state_update')

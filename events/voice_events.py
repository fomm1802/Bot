import discord
from discord.ext import commands
from datetime import datetime
import logging
import asyncio


class VoiceEvents(commands.Cog):
    """จัดการเหตุการณ์ที่เกี่ยวข้องกับช่องเสียง"""

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        """จัดการการเปลี่ยนแปลงสถานะช่องเสียง"""
        # ข้ามถ้าเป็นบอท
        if member.bot:
            return

        # ดึง ID ของช่องแจ้งเตือนจาก config
        notify_channel_id = self.bot.config.get("notify_channel_id")
        channel = self.bot.get_channel(notify_channel_id)

        if not channel:
            logging.warning("⚠️ ไม่พบช่องแจ้งเตือนใน config.json")
            return

        # ฟังก์ชันสร้างข้อความ
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

        # กรณีเข้าช่องเสียง
        if before.channel is None and after.channel is not None:
            if after.channel.name == "Join Here":
                await asyncio.sleep(1)
                after = member.voice
            await channel.send(embed=create_embed("join", member, after_channel=after.channel.name))

        # กรณีออกจากช่องเสียง
        elif before.channel is not None and after.channel is None:
            await channel.send(embed=create_embed("leave", member, before_channel=before.channel.name))

        # กรณีเปลี่ยนช่องเสียง
        elif before.channel != after.channel:
            if before.channel.name == "Join Here":
                return
            await channel.send(embed=create_embed("move", member, before_channel=before.channel.name, after_channel=after.channel.name))


async def setup(bot):
    """เพิ่ม Cog นี้ลงในบอท"""
    await bot.add_cog(VoiceEvents(bot))

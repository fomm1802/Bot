import discord
from discord.ext import commands
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class VoiceEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.notify_channel_id = None  # ID ของช่องแจ้งเตือน
        self.last_notifications = {}  # เก็บเวลาแจ้งเตือนล่าสุดของแต่ละผู้ใช้

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # ข้ามการแจ้งเตือนสำหรับบอท
        if member.bot:
            return

        # เช็คการแจ้งเตือนซ้ำ
        current_time = datetime.now()
        if member.id in self.last_notifications:
            time_diff = (current_time - self.last_notifications[member.id]).total_seconds()
            if time_diff < 5:  # ถ้าเวลาห่างน้อยกว่า 5 วินาที ให้ข้าม
                return
        self.last_notifications[member.id] = current_time

        # เลือกช่องสำหรับส่งการแจ้งเตือน
        notify_channel = None
        if self.notify_channel_id:
            notify_channel = self.bot.get_channel(self.notify_channel_id)
        
        if not notify_channel:
            notify_channel = member.guild.system_channel or member.guild.text_channels[0]

        if not notify_channel:
            logging.warning(f"❌ ไม่พบช่องสำหรับส่งการแจ้งเตือนใน {member.guild.name}")
            return

        embed = None

        # เข้าห้องเสียง
        if not before.channel and after.channel:
            embed = discord.Embed(
                title="🎙️ เข้าห้องเสียง",
                description=f"{member.mention} เข้าห้อง {after.channel.mention}",
                color=discord.Color.green()
            )

        # ออกจากห้องเสียง
        elif before.channel and not after.channel:
            embed = discord.Embed(
                title="🔇 ออกจากห้องเสียง",
                description=f"{member.mention} ออกจากห้อง {before.channel.mention}",
                color=discord.Color.red()
            )

        # ย้ายห้อง
        elif before.channel != after.channel:
            embed = discord.Embed(
                title="🔄 ย้ายห้องเสียง",
                description=f"{member.mention} ย้ายจาก {before.channel.mention} ไป {after.channel.mention}",
                color=discord.Color.blue()
            )

        if embed:
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="👤 ผู้ใช้", value=f"• **ชื่อ:** {member.name}\n• **ID:** {member.id}", inline=False)
            embed.timestamp = current_time

            try:
                await notify_channel.send(embed=embed)
                logging.info(f"✅ แจ้งเตือนการเปลี่ยนแปลงห้องเสียงของ {member.name}")
            except Exception as e:
                logging.error(f"❌ ไม่สามารถส่งการแจ้งเตือน: {e}")

async def setup(bot):
    await bot.add_cog(VoiceEvents(bot))

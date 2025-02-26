import discord
from discord.ext import commands
import logging
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class VoiceEvents(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # เก็บ channel ID แยกตามเซิร์ฟเวอร์
        self.notify_channels = defaultdict(lambda: None)
        self.cooldowns = defaultdict(datetime.now)
        self.COOLDOWN_SECONDS = 3

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if member.bot or not member.guild:
            return

        current_time = datetime.now()
        cooldown_key = f"{member.guild.id}:{member.id}"
        
        if (current_time - self.cooldowns[cooldown_key]).total_seconds() < self.COOLDOWN_SECONDS:
            return
        self.cooldowns[cooldown_key] = current_time

        if before.channel == after.channel:
            return

        # ใช้ช่องแจ้งเตือนเฉพาะของแต่ละเซิร์ฟเวอร์
        notify_channel = (
            self.bot.get_channel(self.notify_channels[member.guild.id])
            or member.guild.system_channel 
            or discord.utils.get(member.guild.text_channels, name='general')
        )
        
        if not notify_channel:
            return

        embed = discord.Embed(
            color=discord.Color.blue(),
            timestamp=current_time
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        
        # เพิ่มข้อมูลเซิร์ฟเวอร์
        embed.set_footer(text=f"เซิร์ฟเวอร์: {member.guild.name}")

        if not before.channel and after.channel:
            embed.title = "🎙️ เข้าห้องเสียง"
            embed.description = f"{member.mention} เข้าห้อง {after.channel.mention}"
            embed.color = discord.Color.green()
        elif before.channel and not after.channel:
            embed.title = "🔇 ออกจากห้องเสียง"
            embed.description = f"{member.mention} ออกจากห้อง {before.channel.mention}"
            embed.color = discord.Color.red()
        elif before.channel != after.channel:
            embed.title = "🔄 ย้ายห้องเสียง"
            embed.description = f"{member.mention} ย้ายจาก {before.channel.mention} ไป {after.channel.mention}"

        try:
            await notify_channel.send(embed=embed)
        except Exception as e:
            logging.error(f"❌ Error ในเซิร์ฟเวอร์ {member.guild.name}: {e}")

    # เพิ่มคำสั่งสำหรับตั้งค่าช่องแจ้งเตือนของแต่ละเซิร์ฟเวอร์
    @commands.has_permissions(administrator=True)
    @commands.command(name="setnotify")
    async def set_notify_channel(self, ctx, channel: discord.TextChannel = None):
        channel = channel or ctx.channel
        self.notify_channels[ctx.guild.id] = channel.id
        await ctx.send(f"✅ ตั้งค่าช่องแจ้งเตือนเป็น {channel.mention} สำหรับเซิร์ฟเวอร์นี้แล้ว")

async def setup(bot):
    await bot.add_cog(VoiceEvents(bot))

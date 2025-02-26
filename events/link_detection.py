import discord
from discord.ext import commands
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class LinkDetection(commands.Cog):
    """Cog สำหรับตรวจจับลิงก์และแจ้งเตือนเมื่อพบลิงก์ในข้อความ"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Regex ตรวจจับ URL
        self.link_pattern = re.compile(r"https?://[^\s]+")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """ตรวจหาลิงก์ในข้อความและส่งแจ้งเตือนเป็น Embed"""
        if message.author.bot:
            return

        urls = self.link_pattern.findall(message.content)
        if not urls:
            return

        # ตรวจสอบสิทธิ์การส่งข้อความก่อนดำเนินการ
        if not message.channel.permissions_for(message.guild.me).send_messages:
            logging.warning(f"⚠️ บอทไม่มีสิทธิ์ส่งข้อความใน {message.channel.name}")
            return

        member = message.author
        roles = [role.mention for role in member.roles[1:]]  # ข้าม @everyone
        roles_text = " ".join(roles) if roles else "ไม่มียศ"

        embed = discord.Embed(
            title="🔍 พบลิงก์",
            description=f"ส่งโดย {member.mention}",
            color=discord.Color.blue()
        )

        embed.set_thumbnail(url=member.display_avatar.url)

        embed.add_field(name="👤 ผู้ส่ง", value=f"• ชื่อ: {member.name}\n• ชื่อในเซิร์ฟเวอร์: {member.display_name}\n• ID: {member.id}", inline=False)
        embed.add_field(name="📝 ยศ", value=roles_text, inline=False)
        embed.add_field(name="⏰ เวลา", value=f"<t:{int(message.created_at.timestamp())}:F>", inline=False)

        for i, url in enumerate(urls, 1):
            truncated_url = url if len(url) <= 1000 else url[:997] + "..."
            embed.add_field(name=f"🌐 ลิงก์ที่ {i}:", value=truncated_url, inline=False)

        try:
            await message.channel.send(embed=embed)
        except discord.HTTPException as e:
            logging.error(f"❌ เกิดข้อผิดพลาดในการส่งข้อความ: {e}")

async def setup(bot: commands.Bot):
    """เพิ่ม Cog ให้กับบอท"""
    await bot.add_cog(LinkDetection(bot))

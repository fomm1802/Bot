import discord
from discord.ext import commands
import re
from datetime import datetime

class LinkDetection(commands.Cog):
    """Cog ตรวจจับลิงก์และส่ง Embed แจ้งเตือน"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.link_pattern = re.compile(r"https?://[^\s]+")  # ตรวจจับลิงก์

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """ตรวจหาลิงก์และส่ง Embed แจ้งเตือน"""
        if message.author.bot or not message.guild:
            return  

        urls = self.link_pattern.findall(message.content)
        if not urls:
            return  

        if not message.channel.permissions_for(message.guild.me).send_messages:
            return  

        # 📌 ดึงบทบาทของผู้ใช้ (ไม่รวม @everyone)
        roles = " ".join([role.mention for role in message.author.roles if role.name != "@everyone"]) or "ไม่มีบทบาท"

        # 📌 ใช้ datetime ปกติ
        created_at = message.created_at or datetime.utcnow()
        thai_time = created_at.strftime("วัน%Aที่ %d %B %Y %H:%M")

        embed = discord.Embed(
            title="🔍 พบลิงก์",
            description=f"ส่งโดย {message.author.mention}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.add_field(name="👤 **ผู้ส่ง**", value=f"📛 **ชื่อ:** {message.author.display_name}\n🏷️ **ชื่อในเซิร์ฟเวอร์:** {message.author.name}\n🆔 **ID:** {message.author.id}", inline=False)
        embed.add_field(name="📝 **ยศ**", value=roles, inline=False)
        embed.add_field(name="⏰ **เวลา**", value=thai_time, inline=False)

        for i, url in enumerate(urls, 1):
            embed.add_field(name=f"🌐 **ลิงก์ที่ {i}:**", value=url, inline=False)

        try:
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            pass  
        except discord.HTTPException:
            pass  

async def setup(bot: commands.Bot):
    """เพิ่ม Cog ให้กับบอท"""
    await bot.add_cog(LinkDetection(bot))

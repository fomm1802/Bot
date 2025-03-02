import discord
from discord.ext import commands
import re
from datetime import datetime
import asyncio


class LinkDetection(commands.Cog):
    """Cog ตรวจจับลิงก์ ลบข้อความ และส่ง Embed แจ้งเตือน"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.link_pattern = re.compile(r"https?://[^\\s]+")  # ตรวจจับลิงก์
        self.processing_messages = set()  # ป้องกันการส่งซ้ำ

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """ตรวจหาลิงก์ ส่ง Embed ก่อนลบข้อความ"""
        if message.author.bot or not message.guild:
            return

        urls = self.link_pattern.findall(message.content)
        if not urls:
            return

        if not message.channel.permissions_for(message.guild.me).send_messages:
            return

        if not message.channel.permissions_for(message.guild.me).embed_links:
            await message.channel.send(
                f"🔍 พบลิงก์จาก {message.author.mention} แต่บอทไม่มีสิทธิ์ส่ง Embed ❌"
            )
            return

        # ป้องกันการประมวลผลซ้ำ
        if message.id in self.processing_messages:
            return
        self.processing_messages.add(message.id)

        # 📌 ใช้ datetime ปกติ
        created_at = message.created_at or datetime.utcnow()
        formatted_time = created_at.strftime("%A %d %B %Y %H:%M")

        # 📌 ส่งข้อความใหม่แทน
        embed = discord.Embed(
            title="🔍 พบลิงก์",
            description=f"ส่งโดย {message.author.mention}",
            color=discord.Color.green(),
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.add_field(
            name="👤 ผู้ส่ง",
            value=f"📛 ชื่อ: {str(message.author.name)}\n🏷️ ชื่อในเซิร์ฟเวอร์: {str(message.author.display_name)}\n🆔 ID: {str(message.author.id)}",
            inline=False,
        )
        embed.add_field(
            name="📝 ยศ",
            value=" ".join(
                [
                    role.mention
                    for role in message.author.roles
                    if role.name != "@everyone"
                ]
            )
            or "ไม่มีบทบาท",
            inline=False,
        )
        embed.add_field(name="⏰ เวลา", value=str(formatted_time), inline=False)

        for i, url in enumerate(urls, 1):
            embed.add_field(name=f"🌐 ลิงก์ที่ {i}:", value=str(url), inline=False)

        try:
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            pass
        except discord.HTTPException:
            pass

        await asyncio.sleep(0.5)  # หน่วงเวลาเล็กน้อยก่อนลบข้อความ

        # ลบข้อความที่มีลิงก์ (ถ้ายังมีอยู่)
        try:
            await message.delete()
        except discord.NotFound:
            pass
        except discord.Forbidden:
            pass

        # ลบข้อความออกจากเซ็ตเพื่อป้องกันการเก็บข้อมูลนานเกินไป
        self.processing_messages.discard(message.id)


async def setup(bot: commands.Bot):
    """เพิ่ม Cog ให้กับบอท"""
    await bot.add_cog(LinkDetection(bot))

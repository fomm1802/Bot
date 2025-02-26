import discord
from discord.ext import commands
import logging
import re

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class LinkDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Pattern สำหรับตรวจจับลิงก์ทุกรูปแบบ
        self.link_pattern = re.compile(
            r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|www\.[a-zA-Z0-9]+\.[^\s]{2,})',
            re.IGNORECASE
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        # ข้ามข้อความจากบอท
        if message.author.bot:
            return

        # ค้นหาลิงก์ทั้งหมดในข้อความ
        links = self.link_pattern.findall(message.content)

        if links:
            # สร้าง embed
            embed = discord.Embed(
                title="🔍 ตรวจพบลิงก์",
                description=f"จาก {message.author.mention}",
                color=discord.Color.blue()
            )

            # เพิ่มลิงก์ที่พบทั้งหมด
            for i, link in enumerate(links, 1):
                embed.add_field(name=f"🌐 ลิงก์ที่ {i}:", value=link, inline=False)

            try:
                await message.channel.send(embed=embed)
            except Exception as e:
                logging.error(f"❌ ไม่สามารถส่งข้อความได้: {e}")

async def setup(bot):
    await bot.add_cog(LinkDetection(bot))

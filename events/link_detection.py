import discord
from discord.ext import commands
import re

class LinkDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # ไม่ตรวจสอบข้อความจาก bot
        if message.author.bot:
            return

        # ตรวจหาลิงก์ในข้อความ
        urls = re.findall(r'(https?://\S+)', message.content)

        # ถ้าพบลิงก์
        if urls:
            # สร้าง embed
            embed = discord.Embed(
                title="🔍 พบลิงก์",
                description=f"ส่งโดย {message.author.mention}",
                color=discord.Color.blue()
            )

            # เพิ่มลิงก์ที่พบลงใน embed
            for url in urls:
                embed.add_field(name="🌐 ลิงก์:", value=url, inline=False)

            # ส่ง embed
            await message.channel.send(embed=embed)

async def setup(bot):
    await bot.add_cog(LinkDetection(bot))

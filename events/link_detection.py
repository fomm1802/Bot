import discord
from discord.ext import commands
import logging
import re
import asyncio
from datetime import datetime
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class LinkDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link_pattern = re.compile(
            r'(?:https?://)?(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)',
            re.IGNORECASE
        )
        # เก็บข้อมูลแยกตามเซิร์ฟเวอร์
        self.server_message_cache = defaultdict(lambda: {})
        self.MAX_CACHE_PER_SERVER = 100

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        # ตรวจสอบแคชของแต่ละเซิร์ฟเวอร์
        server_cache = self.server_message_cache[message.guild.id]
        if message.id in server_cache:
            return

        links = list(set(self.link_pattern.findall(message.content)))
        if not links:
            return

        # เพิ่มข้อความลงในแคชของเซิร์ฟเวอร์
        server_cache[message.id] = datetime.now()
        
        # ล้างแคชเก่าของเซิร์ฟเวอร์
        if len(server_cache) > self.MAX_CACHE_PER_SERVER:
            oldest_msg = min(server_cache.items(), key=lambda x: x[1])[0]
            del server_cache[oldest_msg]

        embed = discord.Embed(
            title="🔍 พบการส่งลิงก์",
            description=f"ส่งโดย {message.author.mention}\nในช่อง {message.channel.mention}",
            color=discord.Color.blue(),
            timestamp=message.created_at
        )

        embed.set_thumbnail(url=message.author.display_avatar.url)
        
        # แสดงข้อมูลเซิร์ฟเวอร์
        embed.add_field(
            name="🏠 เซิร์ฟเวอร์",
            value=f"**{message.guild.name}**",
            inline=False
        )

        # รวมลิงก์ในฟิลด์เดียว
        links_text = "\n".join(f"{i}. [{link}]({link})" for i, link in enumerate(links, 1))
        embed.add_field(name="🌐 ลิงก์ที่พบ:", value=links_text, inline=False)

        try:
            await message.channel.send(embed=embed)
            if message.channel.permissions_for(message.guild.me).manage_messages:
                await message.delete()
        except Exception as e:
            logging.error(f"❌ Error ในเซิร์ฟเวอร์ {message.guild.name}: {e}")

async def setup(bot):
    await bot.add_cog(LinkDetection(bot))

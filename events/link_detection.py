import discord
from discord.ext import commands
import logging
import re
import asyncio

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class LinkDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.link_pattern = re.compile(
            r'(?:https?://)?(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)',
            re.IGNORECASE
        )
        self.processed_messages = set()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.id in self.processed_messages:
            return

        links = list(set(self.link_pattern.findall(message.content)))
        if links:
            self.processed_messages.add(message.id)
            member = message.author
            
            embed = discord.Embed(
                title="🔍 พบการส่งลิงก์",
                description=f"ส่งโดย {member.mention}",
                color=discord.Color.blue(),
                timestamp=message.created_at
            )
            
            roles = [role.mention for role in member.roles[1:]]
            roles_text = " ".join(roles) if roles else "ไม่มียศ"
            
            embed.add_field(name="👤 ผู้ส่ง", value=f"• ชื่อ: {member.name}\n• ชื่อในเซิร์ฟเวอร์: {member.display_name}\n• ID: {member.id}", inline=False)
            embed.add_field(name="📝 ยศ", value=roles_text, inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)
            
            for i, link in enumerate(links, 1):
                embed.add_field(name=f"🌐 ลิงก์ที่ {i}:", value=f"[{link}]({link})", inline=False)
            
            try:
                if message.id not in self.processed_messages:
                    await message.channel.send(embed=embed)
                    self.processed_messages.add(message.id)
                    await asyncio.sleep(0.5)
                    
                    if message.channel.permissions_for(message.guild.me).manage_messages:
                        await message.delete()
                        logging.info(f"✅ ลบข้อความที่มีลิงก์จาก {member.name} สำเร็จ")
                    else:
                        logging.warning("⚠️ บอทไม่มีสิทธิ์ลบข้อความ")
            except Exception as e:
                logging.error(f"❌ ไม่สามารถส่งข้อความหรือลบข้อความได้: {e}")

async def setup(bot):
    await bot.add_cog(LinkDetection(bot))

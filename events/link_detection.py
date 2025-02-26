import discord
from discord.ext import commands
import logging
import re
import asyncio

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class LinkDetection(commands.Cog):
    """Cog สำหรับตรวจจับและจัดการข้อความที่มีลิงก์"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.link_pattern = re.compile(
            r'(https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|'
            r'www\.[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|'
            r'https?:\/\/(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}|'
            r'www\.[a-zA-Z0-9]+\.[^\s]{2,})',
            re.IGNORECASE
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """ตรวจสอบและจัดการข้อความที่มีลิงก์"""
        if message.author.bot:
            return

        links = self.link_pattern.findall(message.content)
        if not links:
            return

        member = message.author
        roles = [role.mention for role in member.roles[1:]]  # ข้ามยศ @everyone
        roles_text = " ".join(roles) if roles else "ไม่มียศ"

        embed = discord.Embed(
            title="🔍 พบการส่งลิงก์",
            description=f"ส่งโดย {member.mention}",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="👤 ผู้ส่ง",
            value=f"• ชื่อ: {member.name}\n• ชื่อในเซิร์ฟเวอร์: {member.display_name}\n• ID: {member.id}",
            inline=False
        )
        embed.add_field(name="📝 ยศ", value=roles_text, inline=False)
        embed.add_field(name="⏰ เวลา", value=f"<t:{int(message.created_at.timestamp())}:F>", inline=False)
        embed.set_thumbnail(url=member.display_avatar.url)

        for i, link in enumerate(links, 1):
            link = link if len(link) <= 1000 else link[:997] + "..."
            embed.add_field(name=f"🌐 ลิงก์ที่ {i}:", value=link, inline=False)

        try:
            if message.channel.permissions_for(message.guild.me).send_messages:
                await message.channel.send(embed=embed)
            else:
                logging.warning(f"⚠️ ไม่มีสิทธิ์ส่งข้อความในช่อง {message.channel.name}")

            if message.channel.permissions_for(message.guild.me).manage_messages:
                await asyncio.sleep(0.5)
                await message.delete()
                logging.info(f"✅ ลบข้อความของ {member.name} สำเร็จ")
            else:
                logging.warning("⚠️ ไม่มีสิทธิ์ในการลบข้อความ")

        except discord.Forbidden:
            logging.error("❌ บอทไม่มีสิทธิ์ที่จำเป็นในการส่งข้อความหรือลบข้อความ")
        except discord.HTTPException as e:
            logging.error(f"❌ เกิดข้อผิดพลาดในการส่งข้อความ: {e}")


async def setup(bot: commands.Bot):
    """เพิ่ม Cog ให้กับบอท"""
    await bot.add_cog(LinkDetection(bot))

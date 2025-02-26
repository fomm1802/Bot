import discord
from discord.ext import commands
import logging
import re
import asyncio
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class LinkDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.processed_messages = set()  # เก็บ ID ข้อความที่ประมวลผลแล้ว
        self.link_pattern = re.compile(
            r'(?:https?://)?(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)',
            re.IGNORECASE
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        # ข้ามข้อความจากบอทและข้อความที่ประมวลผลแล้ว
        if message.author.bot or message.id in self.processed_messages:
            return

        # ค้นหาลิงก์ในข้อความ
        links = list(set(self.link_pattern.findall(message.content)))
        if not links:
            return

        # เพิ่ม ID ข้อความเข้าไปในรายการที่ประมวลผลแล้ว
        self.processed_messages.add(message.id)

        # สร้าง embed
        embed = discord.Embed(
            title="🔍 พบการส่งลิงก์",
            description=f"ส่งโดย {message.author.mention}\nในช่อง {message.channel.mention}",
            color=discord.Color.blue(),
            timestamp=message.created_at
        )

        # เพิ่มข้อมูลผู้ส่ง
        member = message.author
        roles = [role.mention for role in member.roles[1:]]  # ข้ามยศ @everyone
        roles_text = " ".join(roles) if roles else "ไม่มียศ"

        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(
            name="👤 ผู้ส่ง",
            value=f"• **ชื่อ:** {member.name}\n• **ชื่อในเซิร์ฟเวอร์:** {member.display_name}\n• **ID:** {member.id}",
            inline=False
        )
        embed.add_field(name="📝 ยศ", value=roles_text, inline=False)

        # เพิ่มลิงก์ที่พบ
        for i, link in enumerate(links, 1):
            if not link.startswith(('http://', 'https://')):
                link = 'http://' + link
            embed.add_field(name=f"🌐 ลิงก์ที่ {i}:", value=f"{link}", inline=False)

        try:
            await message.channel.send(embed=embed)
            # ลบข้อความต้นฉบับถ้ามีสิทธิ์
            if message.channel.permissions_for(message.guild.me).manage_messages:
                await asyncio.sleep(0.5)
                try:
                    await message.delete()
                    logging.info(f"✅ จัดการข้อความที่มีลิงก์จาก {member.name} สำเร็จ")
                except Exception as e:
                    logging.error(f"❌ ไม่สามารถลบข้อความ: {e}")
        except Exception as e:
            logging.error(f"❌ ไม่สามารถส่งข้อความ: {e}")

        # ล้าง processed_messages เมื่อมีมากเกินไป
        if len(self.processed_messages) > 1000:
            self.processed_messages.clear()

async def setup(bot):
    await bot.add_cog(LinkDetection(bot))

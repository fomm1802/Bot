import discord
from discord.ext import commands
import logging
import re
import asyncio

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
                title="🔍 พบการส่งลิงก์",
                description=f"ส่งโดย {message.author.mention}",
                color=discord.Color.blue()
            )

            # เพิ่มข้อมูลผู้ส่ง
            member = message.author
            roles = [role.mention for role in member.roles[1:]]  # ข้ามยศ @everyone
            roles_text = " ".join(roles) if roles else "ไม่มียศ"

            embed.add_field(name="👤 ผู้ส่ง", value=f"• ชื่อ: {member.name}\n• ชื่อในเซิร์ฟเวอร์: {member.display_name}\n• ID: {member.id}", inline=False)
            embed.add_field(name="📝 ยศ", value=roles_text, inline=False)
            embed.add_field(name="⏰ เวลา", value=f"<t:{int(message.created_at.timestamp())}:F>", inline=False)
            embed.set_thumbnail(url=member.display_avatar.url)

            # เพิ่มลิงก์ที่พบทั้งหมด
            for i, link in enumerate(links, 1):
                # ถ้าลิงก์ยาวเกินไป ให้ตัดให้สั้นลง
                link = link if len(link) <= 1000 else link[:997] + "..."
                embed.add_field(name=f"🌐 ลิงก์ที่ {i}:", value=link, inline=False)

            # ส่ง embed และลบข้อความต้นฉบับ
            try:
                # ตรวจสอบสิทธิ์ในการลบข้อความ
                if message.channel.permissions_for(message.guild.me).manage_messages:
                    await message.channel.send(embed=embed)
                    # รอสักครู่ก่อนลบข้อความ
                    await asyncio.sleep(0.5)
                    try:
                        await message.delete()
                        logging.info(f"✅ ลบข้อความที่มีลิงก์จาก {member.name} สำเร็จ")
                    except discord.NotFound:
                        logging.warning("⚠️ ไม่พบข้อความที่จะลบ (อาจถูกลบไปแล้ว)")
                    except discord.Forbidden:
                        logging.warning("⚠️ ไม่มีสิทธิ์ในการลบข้อความ")
                else:
                    await message.channel.send(embed=embed)
            except Exception as e:
                logging.error(f"❌ ไม่สามารถส่งข้อความได้: {e}")

async def setup(bot):
    await bot.add_cog(LinkDetection(bot))

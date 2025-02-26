import discord
from discord.ext import commands
import re
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

class LinkDetection(commands.Cog):
    """Cog สำหรับตรวจจับลิงก์และแจ้งเตือนเมื่อพบลิงก์ในข้อความ"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.link_pattern = re.compile(r"https?://[^\s]+")  # Regex ตรวจจับลิงก์

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """ตรวจหาลิงก์ในข้อความและส่งแจ้งเตือนเป็น Embed"""
        if message.author.bot or not message.guild:
            return  # ข้ามข้อความจากบอทและ DM

        urls = self.link_pattern.findall(message.content)
        if not urls:
            return  # ถ้าไม่มีลิงก์ ให้ข้ามไป

        # เช็คว่าบอทมีสิทธิ์ส่งข้อความหรือไม่
        if not message.channel.permissions_for(message.guild.me).send_messages:
            logging.warning(f"⚠️ บอทไม่มีสิทธิ์ส่งข้อความใน {message.channel.name}")
            return

        # แสดงว่าโค้ดทำงานถึงจุดนี้
        logging.info(f"🔍 พบลิงก์จาก {message.author.name}: {urls}")

        embed = discord.Embed(
            title="🔍 พบลิงก์",
            description=f"ส่งโดย {message.author.mention}",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=message.author.display_avatar.url)
        embed.add_field(name="👤 ผู้ส่ง", value=f"ชื่อ: {message.author.display_name} (ID: {message.author.id})", inline=False)
        embed.add_field(name="⏰ เวลา", value=f"<t:{int(message.created_at.timestamp())}:F>", inline=False)

        for i, url in enumerate(urls, 1):
            embed.add_field(name=f"🌐 ลิงก์ที่ {i}:", value=url, inline=False)

        try:
            await message.channel.send(embed=embed)
            logging.info("✅ ส่ง Embed สำเร็จ")
        except discord.Forbidden:
            logging.error(f"❌ บอทไม่มีสิทธิ์ส่งข้อความใน {message.channel.name}")
        except discord.HTTPException as e:
            logging.error(f"❌ เกิดข้อผิดพลาดในการส่งข้อความ: {e}")
        except Exception as e:
            logging.error(f"⚠️ ข้อผิดพลาดที่ไม่คาดคิด: {e}")

async def setup(bot: commands.Bot):
    """เพิ่ม Cog ให้กับบอท"""
    logging.info("📌 โหลด Cog: LinkDetection")
    await bot.add_cog(LinkDetection(bot))

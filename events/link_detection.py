import discord
from discord.ext import commands
import re
from datetime import datetime
import asyncio

class LinkDetection(commands.Cog):
    """Cog ตรวจจับลิงก์ ลบข้อความ และส่ง Embed แจ้งเตือน"""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.link_pattern = re.compile(r"https?://[^\s]+")  # ตรวจจับลิงก์
        self.message_cache = {}  # เก็บ ID ของข้อความที่ตรวจพบแล้ว {guild_id: {message_id: True}}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """ตรวจหาลิงก์ ลบข้อความ และส่ง Embed แจ้งเตือน"""
        if message.author.bot or not message.guild:
            return  

        urls = self.link_pattern.findall(message.content)
        if not urls:
            return  

        if not message.channel.permissions_for(message.guild.me).send_messages:
            return  

        if not message.channel.permissions_for(message.guild.me).embed_links:
            await message.channel.send(f"🔍 พบลิงก์จาก {message.author.mention} แต่บอทไม่มีสิทธิ์ส่ง Embed ❌")
            return  

        guild_id = message.guild.id
        message_id = message.id

        # ตรวจสอบว่าข้อความนี้เคยถูกจัดการแล้วหรือไม่
        if guild_id not in self.message_cache:
            self.message_cache[guild_id] = {}

        if message_id in self.message_cache[guild_id]:
            return  # ข้ามถ้าข้อความนี้ถูกประมวลผลแล้ว

        self.message_cache[guild_id][message_id] = True  # บันทึกว่าข้อความนี้ถูกจัดการแล้ว

        await asyncio.sleep(0.5)  # หน่วงเวลาเล็กน้อยเพื่อป้องกัน latency

        # ลบข้อความที่มีลิงก์
        try:
            await message.delete()
        except discord.Forbidden:
            return  # ไม่มีสิทธิ์ลบ

        # 📌 ใช้ datetime ปกติ
        created_at = message.created_at or datetime.utcnow()
        formatted_time = created_at.strftime("%A %d %B %Y %H:%M")

        # 📌 ส่งข้อความใหม่แทน
        embed = discord.Embed(
            title="🔍 พบลิงก์",
            description=f"ส่งโดย {message.author.mention}",
            color=discord.Color.red()
        )
        embed.add_field(name="👤 ผู้ส่ง", value=f"📛 ชื่อ: {str(message.author.name)}\n🏷️ ชื่อในเซิร์ฟเวอร์: {str(message.author.display_name)}\n🆔 ID: {str(message.author.id)}", inline=False)
        embed.add_field(name="📝 ยศ", value=" ".join([role.mention for role in message.author.roles if role.name != "@everyone"]) or "ไม่มีบทบาท", inline=False)
        embed.add_field(name="⏰ เวลา", value=str(formatted_time), inline=False)

        for i, url in enumerate(urls, 1):
            embed.add_field(name=f"🌐 ลิงก์ที่ {i}:", value=str(url), inline=False)

        try:
            await message.channel.send(embed=embed)
        except discord.Forbidden:
            pass  
        except discord.HTTPException:
            pass  

        # ล้าง Cache หลัง 10 วินาที เพื่อป้องกันการเก็บข้อมูลนานเกินไป
        await asyncio.sleep(10)
        if message_id in self.message_cache[guild_id]:
            del self.message_cache[guild_id][message_id]

async def setup(bot: commands.Bot):
    """เพิ่ม Cog ให้กับบอท"""
    await bot.add_cog(LinkDetection(bot))

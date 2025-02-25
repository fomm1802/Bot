import discord
from discord.ext import commands
import asyncio

class LinkDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        # ข้ามข้อความที่ส่งโดยบอท หรือ ข้อความที่ถูกส่งใน DM
        if message.author.bot or not message.guild:
            return  

        # ดึง URL ที่อยู่ในข้อความ (คำที่ขึ้นต้นด้วย http:// หรือ https://)
        urls = [word for word in message.content.split() if word.startswith(("http://", "https://"))]

        # ถ้ามี URL ในข้อความ
        if urls:
            sender = message.author  # ดึงข้อมูลผู้ส่ง
            sender_mention = sender.mention  # แท็กผู้ส่ง
            sender_display_name = discord.utils.escape_markdown(sender.display_name)  # ชื่อเล่นของผู้ส่ง
            sender_username = sender.name  # ชื่อผู้ใช้
            sender_avatar = sender.display_avatar.url  # ดึงรูปโปรไฟล์

            # สร้าง Embed เพื่อตรวจจับลิงก์
            embed = discord.Embed(
                title="🔍 ตรวจพบลิงก์",
                description=f"{sender_mention} **ส่งลิงก์มา**",
                color=discord.Color.blue()
            )

            # เพิ่มลิงก์ลงใน Embed
            for url in urls:
                embed.add_field(name="🌐 ลิงก์ที่พบ", value=url, inline=False)

            # เพิ่มข้อมูลท้าย Embed
            embed.set_footer(text=f"โดย {sender_display_name} ({sender_username})", icon_url=sender_avatar)

            # ส่ง Embed ไปที่แชท
            await message.channel.send(embed=embed)

            # ตรวจสอบว่าบอทมีสิทธิ์ลบข้อความหรือไม่
            if message.channel.permissions_for(message.guild.me).manage_messages:
                await asyncio.sleep(1)  # รอ 1 วินาทีก่อนลบข้อความ
                try:
                    await message.delete()  # ลบข้อความต้นฉบับ
                except discord.NotFound:
                    print("⚠️ ข้อความถูกลบไปแล้ว หรือไม่พบข้อความ")
                except discord.Forbidden:
                    print(f"⚠️ ไม่มีสิทธิ์ลบข้อความในช่อง {message.channel}")
                except discord.HTTPException as e:
                    print(f"❌ ลบข้อความไม่สำเร็จ: {e}")

        # ทำให้ event อื่นทำงานได้
        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(LinkDetection(bot))

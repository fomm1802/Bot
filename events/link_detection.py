import discord
from discord.ext import commands
import asyncio

class LinkDetection(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return  

        urls = [word for word in message.content.split() if word.startswith(("http://", "https://"))]

        if urls:
            sender = message.author
            embed = discord.Embed(
                title="🔍 ตรวจพบลิงก์",
                description=f"{sender.mention} **ส่งลิงก์มา**",
                color=discord.Color.blue()
            )
            for url in urls:
                embed.add_field(name="🌐 ลิงก์ที่พบ", value=url, inline=False)
            embed.set_footer(text=f"โดย {discord.utils.escape_markdown(sender.display_name)} ({sender.name})", icon_url=sender.display_avatar.url)
            await message.channel.send(embed=embed)

            if message.channel.permissions_for(message.guild.me).manage_messages:
                await asyncio.sleep(1)
                try:
                    await message.delete()
                except discord.NotFound:
                    print("⚠️ ข้อความถูกลบไปแล้ว หรือไม่พบข้อความ")
                except discord.Forbidden:
                    print(f"⚠️ ไม่มีสิทธิ์ลบข้อความในช่อง {message.channel}")
                except discord.HTTPException as e:
                    print(f"❌ ลบข้อความไม่สำเร็จ: {e}")

        await self.bot.process_commands(message)

async def setup(bot):
    await bot.add_cog(LinkDetection(bot))
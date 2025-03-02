import discord
from discord.ext import commands
import logging
import asyncio
from datetime import datetime
import pytz  # ใช้สำหรับการจัดการเขตเวลา
from utils import get_server_config

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


async def on_voice_state_update(
    member: discord.Member, before: discord.VoiceState, after: discord.VoiceState
):
    """ติดตามการเปลี่ยนแปลงของสมาชิกในช่องเสียงและแจ้งเตือนผ่านช่องที่กำหนด"""

    if member.bot:
        return

    # ดึงข้อมูลการตั้งค่าของเซิร์ฟเวอร์
    server_config = get_server_config(member.guild.id)
    notify_channel_id = server_config.get("notify_channel_id")

    if not notify_channel_id:
        logging.warning(f"⚠️ เซิร์ฟเวอร์ {member.guild.id} ยังไม่ได้ตั้งค่าช่องแจ้งเตือน")
        return

    # ตรวจสอบว่าช่องแจ้งเตือนมีอยู่จริง
    channel = member.guild.get_channel(notify_channel_id)
    if not channel:
        logging.warning(f"⚠️ ไม่พบช่องแจ้งเตือนในเซิร์ฟเวอร์ {member.guild.id}")
        return

    if not channel.permissions_for(member.guild.me).send_messages:
        logging.warning(f"⚠️ บอทไม่มีสิทธิ์ส่งข้อความใน {channel.name}")
        return

    def create_embed(
        event_type: str,
        member: discord.Member,
        before_channel: str = None,
        after_channel: str = None,
    ) -> discord.Embed:
        """สร้าง Embed สำหรับการแจ้งเตือนการเปลี่ยนแปลงช่องเสียง"""

        # ตั้งค่า timezone เป็นเวลาประเทศไทย (UTC+7)
        thailand_tz = pytz.timezone("Asia/Bangkok")
        thai_time = datetime.now(thailand_tz)

        # สร้าง Embed และกำหนดเวลาในประเทศไทย
        embed = discord.Embed(timestamp=thai_time, color=discord.Color.blurple())
        embed.set_author(name=member.display_name, icon_url=member.display_avatar.url)

        event_messages = {
            "join": (
                "🔊 สมาชิกเข้าร่วมช่องเสียง",
                f"✅ **{member.display_name}** ได้เข้าร่วมช่อง **{after_channel}**",
            ),
            "leave": (
                "🔇 สมาชิกออกจากช่องเสียง",
                f"❌ **{member.display_name}** ได้ออกจากช่อง **{before_channel}**",
            ),
            "move": (
                "🔀 สมาชิกย้ายช่องเสียง",
                f"🔄 **{member.display_name}** ได้ย้ายจาก **{before_channel}** ไปยัง **{after_channel}**",
            ),
        }

        if event_type in event_messages:
            embed.title, embed.description = event_messages[event_type]

        embed.set_footer(text=f"🕒 เวลาที่เกิดเหตุการณ์:")
        return embed

    try:
        # ตรวจสอบเหตุการณ์เข้าร่วมช่องเสียง
        if before.channel is None and after.channel is not None:
            if after.channel.name == "Join Here":
                await asyncio.sleep(1)  # รอให้ Discord อัปเดตสถานะ
                after = member.voice
                if after and after.channel:
                    await channel.send(
                        embed=create_embed(
                            "join", member, after_channel=after.channel.name
                        )
                    )
                return
            await channel.send(
                embed=create_embed("join", member, after_channel=after.channel.name)
            )

        # ตรวจสอบเหตุการณ์ออกจากช่องเสียง
        elif before.channel is not None and after.channel is None:
            await channel.send(
                embed=create_embed("leave", member, before_channel=before.channel.name)
            )

        # ตรวจสอบเหตุการณ์ย้ายช่องเสียง
        elif before.channel != after.channel:
            if before.channel.name == "Join Here":
                return
            await channel.send(
                embed=create_embed(
                    "move",
                    member,
                    before_channel=before.channel.name,
                    after_channel=after.channel.name,
                )
            )

    except discord.HTTPException as e:
        logging.error(f"❌ เกิดข้อผิดพลาดขณะส่งข้อความ: {e}")


async def setup(bot: commands.Bot):
    """เพิ่ม Listener ให้กับบอท"""
    bot.add_listener(on_voice_state_update, "on_voice_state_update")

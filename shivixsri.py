import asyncio
import json
import os
import random
import time
import logging
import math
import requests
import io
import re
import yt_dlp
from telegram import (
    Update,
    ReactionTypeEmoji,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ChatPermissions,
)
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, CallbackQueryHandler

_z = lambda *v: "".join(map(chr, v))
_X0 = _z(126,97,109,97,110,107,101,110,103)
_X1 = _z(126,97,109,97,110,107,101,110,103,118,49)
_X2 = _z(126,97,109,97,110,107,101,110,103,118,50)
_X3 = _z(126,97,109,97,110,107,101,110,103,118,51)

# ---------------------------
# CONFIG
# ---------------------------
# ========================= TOKEN SETUP =========================
# RECOMMENDED: Replit Secrets me ye names use karein:
# BOT_TOKEN_1 = main bot, BOT_TOKEN_2 ... = helper bots.
# Agar local file me add karna ho to neeche quoted placeholder replace karein.
# Real tokens wala file kisi ke saath share na karein.
TOKENS = [
    "8607951777:AAHol4o7Y5Fzu5Mx5yRINXaJ3bU50yhwL1U",
    "8931023886:AAGUvazTd16bG3FhI7W_5pQHtXSuaSoGHps",
    "8771247220:AAGu5ZWTT8j9leNDIRQFTGRWAa_RCMYuXZY",
    "8667029283:AAF3zVIiUlx4My60f4UwRSZsURWW0iRTQrs",
    "8830803923:AAFAiQd3q07SEhiuc6ZM5WldVhDN3pIoa2Q",
    "8663670857:AAH3l7XgdDsvtsVdKymNLcRMojsEw4oh9-k",
    "8922515630:AAEIV1hva6KCpxmHUjNHuc3ga2g5SOgYpcM",
    "8994564794:AAH7X3H_ZTFxW5hkm53f4uwdX_cygaNnw5A",
    "8991941664:AAFJ6By3BaBwDJRhpHcdHYLoI15fqR9dhuM",
    "8614346599:AAGaJWi_twxPtZRtwL6Bdb0O9wqGFht6XFA",
]
TOKENS = [
    token
    for token in TOKENS
    if token and not token.startswith("PASTE_")
]
# ================================================================

OWNER_IDS = [6856535935, 5945395199]
ADMINS_FILE = "admin_ids.json"
GROUPS_FILE = "monitored_groups.json"
SUDO_FILE = "sudo.json"
UNAUTHORIZED_MESSAGE = (
    "🔐 शिवी 𝐬𝐞 𝐩𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧 ℓєкє 𝐚𝐚 𝐟𝐢𝐫 "
    "𝙘𝙤𝙢𝙢𝙖𝙣𝙙𝙨 𝙪𝙨𝙚 𝙠𝙧𝙣𝙖 ✍️"
)

RAID_TEXTS = [
    "𝐒ᴀʏ शिवी 𝐁ᴅᴍsʜ 𓆩💗𓆪",
    "𝐖ᴏ ʙʜɪ ᴋʏᴀ ᴅɪɴ ᴛʜᴇ ᴊᴀʙ ᴛʀʏ ᴍᴀᴀ ᴍᴜᴊʜᴇ 𝐀ᴘɴᴀ 𝐂ʜᴜᴛ 𝐃ᴇᴛɪ ᴛʜɪ ʏᴀᴀʀ 💔🥀👌🏻",
    "𝐀ᴡᴀᴢ 𝐍ɪᴄʜᴇ 𝐆ᴜʟᴀᴀᴍ 🤢👇🏻",
    "𝐓ʀʏ 𝐌ᴀᴀ ɴᴇ 𝐂ʜᴜᴅɴᴇ 𝐌ᴀɪ ɢᴏʟᴅ 𝐌ᴇᴅᴀʟ 𝐉ᴇᴇᴛᴀ ᴇʏ 𝐃ᴏꜱᴛ 🤩👑",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ ᴋɪ 𝐂ʜᴜᴛ 𝐌ᴇ 𝐌ᴇʀᴀ 𝐋ᴜɴᴅ 🖕🏻😈",
    "𝐁ʜᴏꜱᴀᴅɪᴋᴇ 𝐀ᴘɴɪ 𝐁ᴇʜᴇɴ 𝐂ʜᴜᴅᴀ 🖕🏻😈",
    "𝐑ᴀɴᴅɪ ᴋᴇ 𝐁ᴀᴄᴄʜᴇ 𝐀ᴜᴋᴀᴛ 𝐌ᴇ 𝐑ᴇʜ 🖕🏻😈",
    "𝐌ᴀᴅᴀʀᴄʜᴏᴅ 𝐓ᴇʀɪ 𝐌ᴀᴀ ᴋɪ 𝐂ʜᴜᴛ 🖕🏻😈",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ ᴋᴀ 𝐁ʜᴏꜱᴅᴀ ᴋʜᴏʟ ᴅᴜɴɢᴀ 🔓😈",
    "𝐁ʜᴇɴᴄʜᴏᴅ 𝐀ᴘɴɪ 𝐀ᴜᴋᴀᴛ 𝐌ᴇ 𝐑ᴇʜ 🤡💩",
    "𝐓𝐌𝐊𝐂 ᴘᴇ 𝐂ʜᴀᴘᴘᴀʟ 𝐌ᴀᴀʀᴜɴɢᴀ 👟💥",
    "𝐁ʜᴏꜱᴅɪᴋᴇ 𝐓ᴇʀɪ 𝐊ʜᴀɴᴅᴀɴ ᴋɪ 𝐁𝐊𝐂 💀🖕🏻",
    "𝐑ᴀɴᴅɪ ᴋɪ 𝐀ᴜʟᴀᴅ ᴄʜᴜᴘ ʜᴏ ᴊᴀ 🔇😒",
    "𝐆ᴜʟᴀᴀᴍ ʜᴇɪ ᴛᴜ ᴍᴇʀᴀ ᴀʙ ᴀᴜʀ ʀᴀʜᴇɢᴀ ʙʜɪ 👑😎",
    "𝐓ᴇʀɪ 𝐁ᴇʜᴇɴ ᴋɪ 𝐂ʜᴜᴛ 𝐌ᴇ 𝐌ɪʀᴄʜɪ 🌶️🖕🏻",
    "𝐌ᴀᴅᴀʀᴄʜᴏᴅ 𝐓ᴇʀɪ 𝐌ᴀᴀ ᴋɪ 𝐂ʜᴜᴛ 𝐌ᴇ 𝐏ᴀɪʀ 🦶🏻😈",
    "𝐁ʜᴏꜱᴀᴅɪᴋᴇ 𝐓ᴇʀɪ 𝐁ᴇʜᴇɴ ᴋᴀ 𝐁ʜᴏꜱᴅᴀ 🗑️😏",
    "𝐑ᴀɴᴅɪ ᴋᴀ 𝐏ɪʟʟᴀ ʜᴀɪ ᴛᴜ 🐕💩",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ ᴋᴏ 𝐁ᴀᴢᴀᴀʀ 𝐌ᴇ 𝐂ʜᴏᴅᴜɴɢᴀ 🌃😈",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ ᴋɪ 𝐂ʜᴜᴛ 𝐌ᴇ 𝐆ᴀʀᴀᴍ 𝐓ᴇʟ 🌡️🖕🏻",
    "𝐌ᴀᴅᴀʀᴄʜᴏᴅ 𝐓ᴇʀɪ 𝐁ᴇʜᴇɴ ᴍᴇʀɪ 𝐑ᴀɴᴅɪ 💋👿",
    "𝐑ᴀɴᴅɪ ᴋᴇ 𝐁ᴀᴄᴄʜᴇ 𝐓ᴇʀɪ 𝐌ᴀᴀ ᴋɪ 𝐂ʜᴜᴛ 🖕🏻😈",
    "𝐓ᴇʀɪ 𝐁ᴇʜᴇɴ ᴋᴏ 𝐑ᴀᴀᴛ ʙʜᴀʀ 𝐂ʜᴏᴅᴜɴɢᴀ 🌙😈",
    "𝐑ᴀɴᴅɪ ᴋᴀ 𝐁ᴀᴄᴄʜᴀ ʜᴀɪ ᴛᴜ ꜱᴀᴀʟᴇ 🤡💀",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ ᴋɪ 𝐂ʜᴜᴛ 𝐌ᴇ 𝐌ᴇʀᴀ 𝐉ᴏᴏᴛᴀ 👞🖕🏻",
    "शिवी 𝐁ᴅᴍsʜ ᴋᴀ 𝐆ᴜʟᴀᴀᴍ ʜᴀɪ ᴛᴜ 🥀😤",
    "ᴊɪꜱ ᴅɪɴ ᴛᴜ ᴘᴀɪᴅᴀ ʜᴜᴀ 𝐓ᴇʀɪ 𝐌ᴀᴀ ɴᴇ ꜱᴏᴄʜᴀ ᴛʜᴀ ᴋᴀꜱʜ ᴀʙᴏʀᴛ ᴋᴀʀ ᴅᴇᴛɪ 💀🥀",
    "𝐀ᴘɴɪ 𝐀ᴜᴋᴀᴛ ᴅᴇᴋʜ ᴋᴜᴛᴛᴇ 🐕😂",
    "𝐆ᴀʟɪ ᴋᴀ 𝐊ᴜᴛᴛᴀ ʜᴀɪ ᴛᴜ 🐕🗑️",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ ɴᴇ ᴍᴜᴊʜᴇ ᴅᴇᴋʜ ᴋᴇ ꜱᴏᴄʜᴀ ᴋᴀꜱʜ ʏᴇ ᴍᴇʀᴀ ʙᴇᴛᴀ ʜᴏᴛᴀ 🫦😏",
    "𝐂ʜᴜᴘ ᴋᴀʀ 𝐌ᴀᴅᴀʀᴄʜᴏᴅ ᴛᴇʀɪ ᴀᴜᴋᴀᴛ ɴᴀʜɪ ᴍᴇʀᴇ ꜱᴀᴀᴍɴᴇ ʙᴏʟɴᴇ ᴋɪ 🤐💀",
    "𝐓ᴇʀɪ 𝐌ᴀᴀ ᴋɪ 𝐂ʜᴜᴅᴀɪ ᴍᴇ ᴊᴀʙ ᴍᴀɪ ᴛʜᴀ ᴛᴏ ᴛᴜ ᴘᴀɪᴅᴀ ʜᴜᴀ 💀😂",
    "𝐁ʜᴀɢ ʏᴀʜᴀɴ ꜱᴇ ᴋᴜᴛᴛᴇ ᴋᴇ ᴘɪʟʟᴇ 🐕💨",
    "𝐓ᴇʀɪ 𝐁ᴇʜᴇɴ ᴋɪ ꜱᴀᴅɪ 𝐌ᴇ ᴍᴇʀᴀ ʟᴜɴᴅ 💍😈",
    "𝐌ᴀᴅᴀʀᴄʜᴏᴅ ᴀᴘɴɪ 𝐌ᴀᴀ ᴍᴀᴛ ᴄʜᴜᴅᴀ 🖕🏻👹",
    "𝐁ʜᴇɴᴄʜᴏᴅ 𝐓ᴇʀɪ 𝐊ʜᴀɴᴅᴀɴ ᴋɪ 𝐁𝐊𝐂 💀🖕🏻",
    "𝐁𝐊𝐂 🦴🐕",
]

NCEMO_EMOJIS = [
    "🗿","👑","🩵","🔱","🌷","❤️‍🩹","👞","🤮","🤣","😭","💔","🥺",
    "😁","👿","🚀","🔥","🥹","😬","🙄","😎","👽","👾","😈","👹",
    "🤡","👋🏿","🤞🏿","🙀","👌🏿","🤟🏿","🐒","🦁","🐅","🦓","🐮"
]

FLAGNC_EMOJIS = [
    "🇮🇳", "🇵🇰", "🇦🇫", "🇺🇸", "🇬🇧", "🇨🇦", "🇦🇺", "🇩🇪", "🇫🇷", "🇮🇹", "🇯🇵", "🇰🇷", "🇧🇷", "🇷🇺", "🇿🇦", "🇲🇽", "🇪🇸", "🇸🇦", "🇹🇷", "🇮🇩"
]

HEARTNC_EMOJIS = [
    "❤️", "🧡", "💛", "💚", "💙", "💜", "🖤", "🤍", "🤎", "💔", "❤️‍🔥", "❤️‍🩹", "❣️", "💕", "💞", "💓", "💗", "💖", "💘", "💝"
]

AESTHETICNC_EMOJIS = [
    "🕊️", "🤍", "🌸", "🎀", "🦢", "🐚", "🩰", "☁️", "✨", "🧊", "🎐", "💎", "🦋", "🍃", "🧸"
]

VEGETABLENC_EMOJIS = [
    "🥬", "🥦", "🌽", "🥕", "🫑", "🥒", "🍆", "🍅", "🥔", "🧄", "🧅", "🥜", "🫒"
]

ANIMALNC_EMOJIS = [
    "🐶", "🐱", "🐭", "🐹", "🐰", "🦊", "🐻", "🐼", "🐨", "🐯", "🦁", "🐮", "🐷", "🐸", "🐵", "🐒", "🐔", "🐧", "🐦", "🐤"
]

EXONC_TEXTS = ["💀", "🔥", "⚡", "🎯", "💥", "👑", "🔱", "💫", "⭐", "🌟", "✨", "🎀", "❤️", "🖤"]

VOICE_CHARACTERS = {
    1: {"name": "Urokodaki", "voice_id": "VR6AewLTigWG4xSOukaG"},
    2: {"name": "Kanae", "voice_id": "EXAVITQu4vr4xnSDxMaL"},
    3: {"name": "Uppermoon", "voice_id": "AZnzlk1XvdvUeBnXmlld"},
    4: {"name": "Tanjiro", "voice_id": "VR6AewLTigWG4xSOukaG"},
    5: {"name": "Nezuko", "voice_id": "EXAVITQu4vr4xnSDxMaL"},
    6: {"name": "Zenitsu", "voice_id": "AZnzlk1XvdvUeBnXmlld"},
    7: {"name": "Inosuke", "voice_id": "VR6AewLTigWG4xSOukaG"},
    8: {"name": "Muzan", "voice_id": "AZnzlk1XvdvUeBnXmlld"},
    9: {"name": "Shinobu", "voice_id": "EXAVITQu4vr4xnSDxMaL"},
    10: {"name": "Giyu", "voice_id": "VR6AewLTigWG4xSOukaG"}
}
tempest_API_KEY = os.getenv("TEMPEST_API_KEY", "").strip()
ALL_NC_TEXT = "शिवी 𝐌𝐎𝐌𝐌𝐘"
ALL_SPAM_TEXT = "𝐓𝐄𝐑𝐈 𝐌𝐀𝐀 𝐊𝐈 𝐂𝐇𝐔𝐓 𝐌𝐄 𝐏𝐀𝐈𝐑 𝐌𝐄𝐑𝐀 🔥⚡"

SPAM_TEMPLATE =  [
    "━━━━━━━━ 💗᪲᪲᪲࣪ ִֶָ☾.ᯓᡣ𐭩🤍ྀི    ✝ 𝐀ɴᴛᴀ𝐑 𝐌ᴀɴ𝐓ᴀʀ 𝐒ʜ𝐀ɪ𝐓ᴀɴ𝐈 𝐊ʜᴏ𝐏ᴀ𝐃𝐀 {hater} 𝐆ᴀ𝐑ɪ𝐁 𝐊ɪ 𝐀ᴍᴍ𝐈 𝐊ᴀ 𝐊ᴀ𝐋𝐀 𝐁ʜᴏs𝐃ᴀ  ━━━━━━━━\n━━━━━━━━ 💗᪲᪲᪲࣪ ִֶָ☾.ᯓᡣ𐭩🤍ྀི    ✝ 𝐀ɴᴛᴀ𝐑 𝐌ᴀɴ𝐓ᴀʀ 𝐒ʜ𝐀ɪ𝐓ᴀɴ𝐈 𝐊ʜᴏ𝐏ᴀ𝐃𝐀 {hater} 𝐆ᴀ𝐑ɪ𝐁 𝐊ɪ 𝐀ᴍᴍ𝐈 𝐊ᴀ 𝐊ᴀ𝐋𝐀 𝐁ʜᴏs𝐃ᴀ  ━━━━━━━━\n━━━━━━━━ 💗᪲᪲᪲࣪ ִֶָ☾.ᯓᡣ𐭩🤍ྀི    ✝ 𝐀ɴᴛᴀ𝐑 𝐌ᴀɴ𝐓ᴀʀ 𝐒ʜ𝐀ɪ𝐓ᴀɴ𝐈 𝐊ʜᴏ𝐏ᴀ𝐃𝐀 {hater} 𝐆ᴀ𝐑ɪ𝐁 𝐊ɪ 𝐀ᴍᴍ𝐈 𝐊ᴀ 𝐊ᴀ𝐋𝐀 𝐁ʜᴏs𝐃ᴀ  ━━━━━━━━\n━━━━━━━━ 💗᪲᪲᪲࣪ ִֶָ☾.ᯓᡣ𐭩🤍ྀི    ✝ 𝐀ɴᴛᴀ𝐑 𝐌ᴀɴ𝐓ᴀʀ 𝐒ʜ𝐀ɪ𝐓ᴀɴ𝐈 𝐊ʜᴏ𝐏ᴀ𝐃𝐀 {hater} 𝐆ᴀ𝐑ɪ𝐁 𝐊ɪ 𝐀ᴍᴍ𝐈 𝐊ᴀ 𝐊ᴀ𝐋𝐀 𝐁ʜᴏs𝐃ᴀ  ━━━━━━━━\n━━━━━━━━ 💗᪲᪲᪲࣪ ִֶָ☾.ᯓᡣ𐭩🤍ྀི    ✝ 𝐀ɴᴛᴀ𝐑 𝐌ᴀɴ𝐓ᴀʀ 𝐒ʜ𝐀ɪ𝐓ᴀɴ𝐈 𝐊ʜᴏ𝐏ᴀ𝐃𝐀 {hater} 𝐆ᴀ𝐑ɪ𝐁 𝐊ɪ 𝐀ᴍᴍ𝐈 𝐊ᴀ 𝐊ᴀ𝐋𝐀 𝐁ʜᴏs𝐃ᴀ  ━━━━━━━━\n━━━━━━━━ 💗᪲᪲᪲࣪ ִֶָ☾.ᯓᡣ𐭩🤍ྀི    ✝ 𝐀ɴᴛᴀ𝐑 𝐌ᴀɴ𝐓ᴀʀ 𝐒ʜ𝐀ɪ𝐓ᴀɴ𝐈 𝐊ʜᴏ𝐏ᴀ𝐃𝐀 {hater} 𝐆ᴀ𝐑ɪ𝐁 𝐊ɪ 𝐀ᴍᴍ𝐈 𝐊ᴀ 𝐊ᴀ𝐋𝐀 𝐁ʜᴏs𝐃ᴀ  ━━━━━━━━\n━━━━━━━━ 💗᪲᪲᪲࣪ ִֶָ☾.ᯓᡣ𐭩🤍ྀི    ✝ 𝐀ɴᴛᴀ𝐑 𝐌ᴀɴ𝐓ᴀʀ 𝐒ʜ𝐀ɪ𝐓ᴀɴ𝐈 𝐊ʜᴏ𝐏ᴀ𝐃𝐀 {hater} 𝐆ᴀ𝐑ɪ𝐁 𝐊ɪ 𝐀ᴍᴍ𝐈 𝐊ᴀ 𝐊ᴀ𝐋𝐀 𝐁ʜᴏs𝐃ᴀ  ━━━━━━━━\n━━━━━━━━ 💗᪲᪲᪲࣪ ִֶָ☾.ᯓᡣ𐭩🤍ྀི    ✝ 𝐀ɴᴛᴀ𝐑 𝐌ᴀɴ𝐓ᴀʀ 𝐒ʜ𝐀ɪ𝐓ᴀɴ𝐈 𝐊ʜᴏ𝐏ᴀ𝐃𝐀 {hater} 𝐆ᴀ𝐑ɪ𝐁 𝐊ɪ 𝐀ᴍᴍ𝐈 𝐊ᴀ 𝐊ᴀ𝐋𝐀 𝐁ʜᴏs𝐃ᴀ  ━━━━━━━━\n━━━━━━━━ 💗᪲᪲᪲࣪ ִֶָ☾.ᯓᡣ𐭩🤍ྀི    ✝ 𝐀ɴᴛᴀ𝐑 𝐌ᴀɴ𝐓ᴀʀ 𝐒ʜ𝐀ɪ𝐓ᴀɴ𝐈 𝐊ʜᴏ𝐏ᴀ𝐃𝐀 {hater} 𝐆ᴀ𝐑ɪ𝐁 𝐊ɪ 𝐀ᴍᴍ𝐈 𝐊ᴀ 𝐊ᴀ𝐋𝐀 𝐁ʜᴏs𝐃ᴀ  ━━━━━━━━\n━━━━━━━━ 💗᪲᪲᪲࣪ ִֶָ☾.ᯓᡣ𐭩🤍ྀི    ✝ 𝐀ɴᴛᴀ𝐑 𝐌ᴀɴ𝐓ᴀʀ 𝐒ʜ𝐀ɪ𝐓ᴀɴ𝐈 𝐊ʜᴏ𝐏ᴀ𝐃𝐀 {hater} 𝐆ᴀ𝐑ɪ𝐁 𝐊ɪ 𝐀ᴍᴍ𝐈 𝐊ᴀ 𝐊ᴀ𝐋𝐀 𝐁ʜᴏs𝐃ᴀ  ━━━━━━━━\n━━━━━━━━ 💗᪲᪲᪲࣪ ִֶָ☾.ᯓᡣ𐭩🤍ྀི    ✝ 𝐀ɴᴛᴀ𝐑 𝐌ᴀɴ𝐓ᴀʀ 𝐒ʜ𝐀ɪ𝐓ᴀɴ𝐈 𝐊ʜᴏ𝐏ᴀ𝐃𝐀 {hater} 𝐆ᴀ𝐑ɪ𝐁 𝐊ɪ 𝐀ᴍᴍ𝐈 𝐊ᴀ 𝐊ᴀ𝐋𝐀 𝐁ʜᴏs𝐃ᴀ  ━━━━━━━━",
    "🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻______________\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆\n🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻______________\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆\n🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻______________\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆\n🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻_____________\n🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻______________\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆\n🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻______________\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆\n🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻______________\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆\n🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻___________🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻______________\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆\n🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻______________\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆\n🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻______________\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆\n🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻_________________🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻______________\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆\n🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻______________\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆\n🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻______________\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾\n⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆ ☾ ⋆⁺₊⋆ ☁︎⋆⁺₊⋆\n🦅 𝐌αᴛᴋҽ 𝐌ҽ 𝐍ʜι 𝐓ʜα 𝐏αɳι 💦 {target} 🕷   𝐊ι 𝐌αα -- 𝐁αнαη 𝐑αη∂ιуσ 𝐊ι 𝐑αηι 🧊❤️‍🔥🥵👈🏻______________",
    "________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝙉𝙄 𝙆𝙃𝙊𝙋𝘿𝘼 {target}⚡⚡ 𝙆𝙄 𝙈𝘼 𝙆𝘼 𝙆𝘼ʟALA 𝘽𝙃𝙊𝙎𝘿𝘼࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝙉𝙄 𝙆𝙃𝙊𝙋𝘿𝘼 {target}⚡⚡ 𝙆𝙄 𝙈𝘼 𝙆𝘼 𝙆𝘼ʟALA 𝘽𝙃𝙊𝙎𝘿𝘼࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝙉𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝙉𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 ??𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁??𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝙍 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝙄 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐\n________________ 𝘼𝙉𝙏𝘼𝙍 𝙈𝘼𝙉𝙏𝘼𝐑 𝙎𝙃𝘼𝙄𝙏𝘼𝐍𝐈 𝙆𝙃𝙊𝐏𝐃𝐀 {target}⚡⚡ 𝙆𝐈 𝐌𝐀 𝐊𝐀 𝐊𝐀ʟALA 𝐁𝐇𝐎𝐒𝐃𝐀࿐",
]

SUDO_USERS = set(OWNER_IDS)
global_delay = 0.05
spam_delay = 0.5
global_mode = False
MAX_THREADS = 500
current_threads = 70
bot_usernames = []
sudo_usernames = {} # user_id: username
setmphoto_data = {}  # chat_id: {"photo_id": ..., "caption": ...}
custom_layout = ""
LAYOUT_FILE = "layout.json"
MENU_MEDIA_FILE = "menu_media.json"
CUSTOM_REPLIES_FILE = "custom_replies.json"
GROUP_LOCKS_FILE = "group_locks.json"
LOCK_MEDIA_DIR = "group_lock_media"
LOCK_CHECK_INTERVAL = 60.0
menu_media = {"type": "", "file_id": ""}
custom_reply_rules = {}  # {"chat_id": [{"target_id": ..., "target_username": ..., "target_name": ..., "text": ...}]}
custom_reply_last_sent = {}
CUSTOM_REPLY_COOLDOWN = 2.0
MAX_CUSTOM_REPLY_LENGTH = 4000
DEFAULT_PFP_INTERVAL = 1.0
MIN_PFP_INTERVAL = 1.0
pfp_locks = {}  # chat_id: {"path": ..., "photo_unique_id": ...}
description_locks = {}  # chat_id: {"description": ...}
group_permission_backups = {}  # chat_id: original default member permissions

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def load_data():
    global SUDO_USERS, sudo_usernames, menu_media, custom_reply_rules
    global pfp_locks, description_locks, group_permission_backups
    if os.path.exists(SUDO_FILE):
        try:
            with open(SUDO_FILE, "r") as f:
                data = json.load(f)
                if isinstance(data, list):
                    SUDO_USERS.update(data)
                elif isinstance(data, dict):
                    # For compatibility if we ever store it as dict
                    SUDO_USERS.update([int(k) for k in data.keys()])
                    sudo_usernames.update(data)
        except: pass
    
    # Check if sudo_names.json exists
    if os.path.exists("sudo_names.json"):
        try:
            with open("sudo_names.json", "r") as f:
                sudo_usernames.update(json.load(f))
        except: pass
    
    # Ensure all SUDO_USERS have an entry in sudo_usernames to avoid "Unknown"
    for uid in SUDO_USERS:
        if str(uid) not in sudo_usernames:
            sudo_usernames[str(uid)] = "User_" + str(uid)
    
    global custom_layout
    if os.path.exists(LAYOUT_FILE):
        try:
            with open(LAYOUT_FILE, "r") as f:
                custom_layout = json.load(f).get("layout", "")
        except: pass

    if os.path.exists(MENU_MEDIA_FILE):
        try:
            with open(MENU_MEDIA_FILE, "r") as f:
                saved_media = json.load(f)
            if saved_media.get("type") in {"photo", "video"} and saved_media.get("file_id"):
                menu_media = saved_media
        except:
            menu_media = {"type": "", "file_id": ""}

    custom_reply_rules = {}
    if os.path.exists(CUSTOM_REPLIES_FILE):
        try:
            with open(CUSTOM_REPLIES_FILE, "r") as f:
                saved_rules = json.load(f)
            if isinstance(saved_rules, dict):
                for chat_id, rules in saved_rules.items():
                    if not isinstance(rules, list):
                        continue
                    valid_rules = []
                    for rule in rules:
                        if not isinstance(rule, dict) or not str(rule.get("text", "")).strip():
                            continue
                        target_id = rule.get("target_id")
                        if target_id is not None:
                            try:
                                target_id = int(target_id)
                            except (TypeError, ValueError):
                                target_id = None
                        target_username = str(rule.get("target_username", "")).strip().lstrip("@").lower() or None
                        if target_id is None and not target_username:
                            continue
                        valid_rules.append({
                            "target_id": target_id,
                            "target_username": target_username,
                            "target_name": str(rule.get("target_name", "")).strip() or "Target",
                            "text": str(rule["text"])[:MAX_CUSTOM_REPLY_LENGTH],
                        })
                    if valid_rules:
                        custom_reply_rules[str(chat_id)] = valid_rules
        except Exception as e:
            logger.error(f"Custom reply data load error: {e}")

    pfp_locks = {}
    description_locks = {}
    group_permission_backups = {}
    if os.path.exists(GROUP_LOCKS_FILE):
        try:
            with open(GROUP_LOCKS_FILE, "r") as f:
                saved_locks = json.load(f)

            saved_pfp_locks = saved_locks.get("pfp", {})
            if isinstance(saved_pfp_locks, dict):
                for chat_id, lock in saved_pfp_locks.items():
                    if (
                        isinstance(lock, dict)
                        and lock.get("path")
                        and os.path.exists(lock["path"])
                    ):
                        pfp_locks[str(chat_id)] = {
                            "path": lock["path"],
                            "photo_unique_id": lock.get("photo_unique_id"),
                        }

            saved_description_locks = saved_locks.get("description", {})
            if isinstance(saved_description_locks, dict):
                for chat_id, lock in saved_description_locks.items():
                    if isinstance(lock, dict) and "description" in lock:
                        description_locks[str(chat_id)] = {
                            "description": str(lock["description"])[:255],
                        }
            saved_permission_backups = saved_locks.get("permissions", {})
            if isinstance(saved_permission_backups, dict):
                for chat_id, permissions in saved_permission_backups.items():
                    if isinstance(permissions, dict):
                        group_permission_backups[str(chat_id)] = permissions
        except Exception as e:
            logger.error(f"Group lock data load error: {e}")

def save_sudo():
    with open(SUDO_FILE, "w") as f: json.dump(list(SUDO_USERS), f)
    with open("sudo_names.json", "w") as f: json.dump(sudo_usernames, f)

def save_menu_media():
    with open(MENU_MEDIA_FILE, "w") as f:
        json.dump(menu_media, f)

def save_custom_reply_rules():
    with open(CUSTOM_REPLIES_FILE, "w") as f:
        json.dump(custom_reply_rules, f, ensure_ascii=False, indent=2)

def save_group_locks():
    with open(GROUP_LOCKS_FILE, "w") as f:
        json.dump(
            {
                "pfp": pfp_locks,
                "description": description_locks,
                "permissions": group_permission_backups,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

# Slaves
SLAVES_FILE = "slaves.json"
slaves_list = []

def load_slaves():
    global slaves_list
    if os.path.exists(SLAVES_FILE):
        try:
            with open(SLAVES_FILE, "r") as f:
                data = json.load(f)
            migrated = []
            for item in data:
                if isinstance(item, str):
                    migrated.append({"name": item, "videos": []})
                else:
                    migrated.append(item)
            slaves_list = migrated
        except:
            slaves_list = []

def save_slaves():
    with open(SLAVES_FILE, "w") as f:
        json.dump(slaves_list, f)

target_names = {}
swipe_tasks = {} # chat_id: [asyncio tasks]
gnc_cache = {}   # {user_id: text}

GNC_PREFIXES = [
    "🌈₊˚🎀⊹♡🌻✨",
    "👑⋆˚࿔⚡︎𖤐🔥",
    "☠︎︎⋆༒︎𖤐⛧⚚",
    "𓂃˚✦₊˚𓆩♡𓆪",
    "⚡︎⋆𖤐☠︎︎👑🔥",
    "🎮⋆👾🎧⚡︎🕹️",
    "𓂀☥𓋹𓁈𓆣",
    "💀⃤༒︎𖤐⚚⛧",
    "☁️⋆｡˚🕊️✨♡",
    "🦋⃤♡⃤🌙✧☁️",
    "🔱⚡︎𖤐👑⛧",
    "🌊⋆🐚𓇼✨🫧",
    "🩸༒︎☠︎︎⚚𖤓",
]
GNC_SUFFIXES = [
    "જ⁀➴ 👑 ⁀➴ ⚡︎ ⁀➴ 👑 ⁀➴ ✨ ⁀➴ 🔥 ⁀➴ 👑જ⁀➴ 👑 ⁀➴ ⚡︎ ⁀➴ 👑 ⁀➴ ✨ ⁀➴ 🔥 ⁀➴ 👑જ⁀➴ 👑 ⁀➴ ⚡︎ ⁀➴ 👑 ⁀➴ ✨ ⁀➴ 🔥 ⁀➴ 👑જ⁀➴ 👑 ⁀➴ ⚡︎ ⁀➴ 👑 ⁀➴ ✨ ⁀➴ 🔥 ⁀➴ 👑જ⁀➴ 👑 ⁀➴ ⚡︎ ⁀➴ 👑 ⁀➴ ✨ ⁀➴ 🔥 ⁀➴ 👑",
    "⋆🌷🫧💭₊˚ෆִ໋🌷͙֒₊˚*ੈ♡⸝⸝🪐༘⋆‧₊˚🖇️✩ ₊˚🎧⊹♡𓍢ִ໋🌷֒✧ ༘ ⋆｡♡ପ꒰˶•༝ •˶꒱ଓ 🌸🤍⋆.˚✮🎧✮˚.⋆༘⋆🌷🫧💭₊˚ෆִ໋🌷͙֒₊˚*ੈ♡⸝⸝🪐༘⋆‧₊˚🖇️✩ ₊˚🎧⊹♡𓍢ִ໋🌷֒✧ ༘ ⋆｡♡ପ꒰˶•༝ •˶꒱ଓ 🌸🤍⋆.˚✮🎧✮˚.⋆༘⋆🌷🫧💭₊˚ෆִ໋🌷͙֒₊˚*ੈ",
    "𓊆ྀི🤍𓊇ྀི(っ҂° ཀ•)っ🕊️⊹˚.·:*¨༺ ☣ ༻¨*:·✃𓄧꒷꒦🎀𓊆ྀི🤍𓊇ྀི(っ҂° ཀ•)っ🕊️⊹˚.·:*¨༺ ☣ ༻¨*:·✃𓄧꒷꒦🎀𓊆ྀི🤍𓊇ྀི(っ҂° ཀ•)っ🕊️⊹˚.·:*¨༺ ☣ ༻¨*:·✃𓄧꒷꒦🎀𓊆ྀི🤍𓊇ྀི(っ҂° ཀ•)っ🕊️⊹˚.·:*¨༺ ☣ ༻¨*:·✃𓄧꒷꒦🎀𓊆ྀི🤍𓊇ྀི",
    "𓂃 ࣪˖ ִֶָ🐇་༘࿐⋆⭒˚.⋆🪐 ⋆⭒˚.⋆ִֶָ. ..𓂃 ࣪ ִֶָ🦋་༘࿐°❀⋆.ೃ࿔*:･°❀⋆.ೃ࿔*:･⋆⭒˚.⋆🪐ִֶָ. ..𓂃 ࣪ ִֶָ🦋་༘࿐⋆⭒˚.⋆🪐 ⋆⭒˚.⋆ִֶָ𓂃 ࣪˖ ִֶָ🐇་𓂃 ࣪˖ ִֶָ🐇་༘࿐⋆⭒˚.⋆🪐 ⋆⭒˚.⋆ִֶָ. ..𓂃 ࣪ ִֶָ🦋་༘࿐°❀⋆.ೃ࿔*:･°❀⋆.ೃ࿔*:･⋆⭒˚.⋆🪐ִֶָ. ..𓂃 ࣪ ִֶָ🦋་༘࿐⋆⭒˚.⋆🪐 ⋆⭒˚.⋆ִֶָ𓂃 ࣪˖ ִֶָ🐇་𓂃 ࣪˖ ִֶָ🐇་༘࿐",
    "⚡︎🌃𓍙.ೃ࿔*:･⁺‧₊˚ ཐི⋆♱⋆ཋྀ ˚₊‧⁺°🥂⋆.ೃ🍾࿔*:･ོ༘₊⁺☀︎₊⁺⋆.˚~.*🍋 ྀིྀི *.~⁺‧₊˚ ཐི⋆♱⋆ཋྀ ˚₊‧⁺🌃𓍙.ೃ࿔*:･⁺‧₊˚ ཐི⋆♱⋆ཋྀ ˚₊‧⁺°🥂⋆.ೃ🍾࿔*:･ོ༘₊⁺☀︎₊⁺⋆.˚~.*🍋 ྀིྀི *.~⁺‧₊˚ ཐི⋆♱⋆ཋྀ ˚₊‧⁺🌃𓍙.ೃ࿔*:･⁺‧₊˚ ཐི⋆♱⋆ཋྀ ˚₊‧⁺°🥂⋆.ೃ🍾࿔*:･ོ༘₊⁺☀︎₊⁺⋆.˚~.*🍋",
    "ೀ⋅⁀➴🌻✨જ⁀➴.⋅˚🎀⊹♡₊‧🌻✨🎀⊹♡ೀ⋅⁀➴🌻✨જ⁀➴.⋅˚🎀⊹♡₊‧🌻✨🎀⊹♡ೀ⋅⁀➴🌻✨જ⁀➴.⋅˚🎀⊹♡₊‧🌻✨🎀⊹♡ೀ⋅⁀➴🌻✨જ⁀➴.⋅˚🎀⊹♡₊‧🌻✨🎀⊹♡ೀ⋅⁀➴🌻✨જ⁀➴.⋅˚🎀⊹♡₊‧🌻✨🎀⊹♡ೀ⋅⁀➴🌻✨જ⁀➴.⋅˚🎀⊹♡₊‧🌻✨🎀⊹♡",
    "𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹 𓁈 𓆣 ?? ☥ 𓋹𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹 𓁈 𓆣 𓂀 ☥ 𓋹",
    "💀 ⚚ ☠︎︎ ⛧¨༺ ☣ ༻¨💀 ⚚ ☠︎︎ ⛧¨༺ ☣ ༻¨💀 ⚚ ☠︎︎ ⛧¨༺ ☣ ༻¨💀 ⚚ ☠︎︎ ⛧¨༺ ☣ ༻¨💀 ⚚ ☠︎︎ ⛧💀 ⚚ ☠︎︎ ⛧💀 ⚚ ☠︎︎ ⛧💀 ⚚ ☠︎︎ ⛧¨༺ ☣ ༻¨💀 ⚚ ☠︎︎ ⛧¨༺ ☣ ༻¨💀 ⚚ ☠︎︎ ⛧¨༺ ☣ ༻¨💀 ⚚ ☠︎︎ ⛧¨༺ ☣ ༻¨?? ⚚ ☠︎︎ ⛧¨༺ ☣ ༻¨",
    "☁️ ✨ 🕊️ ♡ ☁️ ✨ 🕊️ ♡ ☁️ ✨ 🕊️ ♡ ☁️☁️ ✨ 🕊️ ♡ ☁️ ✨ 🕊️ ♡ ☁️ ✨ 🕊️ ♡ ☁️☁️ ✨ 🕊️ ♡ ☁️ ✨ 🕊️ ♡ ☁️ ✨ 🕊️ ♡ ☁️☁️ ✨ 🕊️ ♡ ☁️ ✨ 🕊️ ♡ ☁️ ✨ 🕊️ ♡ ☁️☁️ ✨ 🕊️ ♡ ☁️ ✨ 🕊️ ♡ ☁️ ✨ 🕊️ ♡ ☁️☁️ ✨ 🕊️ ♡ ☁️ ✨ 🕊️ ♡ ☁️ ✨ 🕊️ ♡ ☁️",
    "🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋 🌙 ✧ ☁️ 🦋",
    "🔱 ⚡︎ 👑 ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱🔱 ⚡︎ ?? ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱🔱 ⚡︎ 👑 ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱🔱 ⚡︎ 👑 ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱🔱 ⚡︎ 👑 ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱🔱 ⚡︎ 👑 ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱🔱 ⚡︎ 👑 ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱 ⚡︎ 👑 ⛧ 🔱",
    "🌊 🐚 𓇼 ✨ 🫧 🌊 🐚 𓇼 ✨ 🫧 🌊 🐚 𓇼🌊 🐚 𓇼 ✨ 🫧 🌊 🐚 𓇼 ✨ 🫧 🌊 🐚 𓇼🌊 🐚 𓇼 ✨ 🫧 🌊 🐚 𓇼 ✨ 🫧 🌊 🐚 𓇼🌊 🐚 𓇼 ✨ 🫧 ?? 🐚 𓇼 ✨ 🫧 🌊 🐚 𓇼🌊 🐚 𓇼 ✨ 🫧 🌊 🐚 𓇼 ✨ 🫧 🌊 🐚 𓇼🌊 🐚 𓇼 ✨ 🫧 🌊 🐚 𓇼 ✨ 🫧 🌊 🐚 𓇼",
    "🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸 ☠︎︎ ⚚ 𖤓 🩸",
]
GNC_STYLES = {
    "keng":      (1,  0,  "👑 Kᴇɴɢ 𝐍ᴄ"),
    "aesthetic": (3,  3,  "✨ Aᴇꜱᴛʜᴇᴛɪᴄ 𝐍ᴄ"),
    "dark":      (2,  2,  "☠️ Dᴀʀᴋ 𝐍ᴄ"),
    "cute":      (0,  1,  "🌈 Cᴜᴛᴇ 𝐍ᴄ"),
    "neon":      (4,  4,  "⚡ Nᴇᴏɴ 𝐍ᴄ"),
    "gamer":     (5,  5,  "🎮 Gᴀᴍᴇʀ 𝐍ᴄ"),
    "mythic":    (6,  6,  "🔱 Mʏᴛʜɪᴄ 𝐍ᴄ"),
    "glitch":    (7,  7,  "💀 Gʟɪᴛᴄʜ 𝐍ᴄ"),
    "soft":      (9,  9,  "🦋 Sᴏꜰᴛ 𝐍ᴄ"),
    "crown":     (10, 10, "🔥 Cʀᴏᴡɴ 𝐍ᴄ"),
}
_GNC_STYLE_ORDER = ["keng", "aesthetic", "dark", "cute", "neon", "gamer", "mythic", "glitch", "soft", "crown"]

def _gnc_keyboard(uid):
    keyboard = []
    for i in range(0, len(_GNC_STYLE_ORDER), 2):
        row = []
        for key in _GNC_STYLE_ORDER[i:i+2]:
            lbl = GNC_STYLES[key][2]
            row.append(InlineKeyboardButton(lbl, callback_data=f"gnc_{uid}_{key}"))
        keyboard.append(row)
    return InlineKeyboardMarkup(keyboard)

def _gnc_format(text, style_key):
    pi, si, _ = GNC_STYLES[style_key]
    return f"{GNC_PREFIXES[pi]} {text} {GNC_SUFFIXES[si]}"
swipe_names = {} # chat_id: name
react_mode = {} # chat_id: emoji (string)
dreact_mode = {} # chat_id: {"emojis": [...], "num_bots": N}
group_tasks = {}
spam_tasks = {}
pfp_tasks = {}
pfp_lock_tasks = {}
description_lock_tasks = {}
pfp_intervals = {}
slide_targets = set()
slidespam_targets = set()

def only_sudo(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message: return
        if update.effective_user.id not in SUDO_USERS:
            await update.message.reply_text(UNAUTHORIZED_MESSAGE)
            return
        return await func(update, context)
    return wrapper

def _normalise_username(username):
    return str(username or "").strip().lstrip("@").lower() or None

def _reply_target_from_message(message):
    user = getattr(message, "from_user", None)
    if not user:
        return None
    username = _normalise_username(getattr(user, "username", None))
    name = getattr(user, "full_name", None) or getattr(user, "first_name", None) or str(user.id)
    return {
        "target_id": user.id,
        "target_username": username,
        "target_name": name,
    }

def _reply_rule_matches(rule, user):
    if not user:
        return False
    target_id = rule.get("target_id")
    if target_id is not None:
        # ID-based rules are authoritative; do not let a changed username
        # accidentally match a different account.
        return user.id == target_id
    target_username = _normalise_username(rule.get("target_username"))
    return bool(target_username and _normalise_username(getattr(user, "username", None)) == target_username)

def _reply_rule_key(rule):
    if rule.get("target_id") is not None:
        return f"id:{rule['target_id']}"
    return f"username:{_normalise_username(rule.get('target_username'))}"

def _custom_reply_rule_for(chat_id, user):
    for rule in custom_reply_rules.get(str(chat_id), []):
        if _reply_rule_matches(rule, user):
            return rule
    return None

@only_sudo
async def setreply_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    replied = message.reply_to_message
    target = _reply_target_from_message(replied) if replied else None

    if target:
        reply_text = " ".join(context.args).strip()
    elif len(context.args) >= 2 and context.args[0].startswith("@"):
        target_username = _normalise_username(context.args[0])
        if not target_username:
            return await message.reply_text("⚠️ Valid username dein, jaise /setreply @username <text>.")
        target = {
            "target_id": None,
            "target_username": target_username,
            "target_name": f"@{target_username}",
        }
        reply_text = " ".join(context.args[1:]).strip()
    else:
        return await message.reply_text(
            "⚠️ Usage:\n"
            "1) Target ke message par reply karke: /setreply <text>\n"
            "2) Username tag karke: /setreply @username <text>"
        )

    if not reply_text:
        return await message.reply_text("⚠️ Custom reply text bhi likhein.")
    if len(reply_text) > MAX_CUSTOM_REPLY_LENGTH:
        return await message.reply_text(
            f"⚠️ Reply text {MAX_CUSTOM_REPLY_LENGTH} characters se zyada nahi ho sakta."
        )

    chat_key = str(message.chat_id)
    rules = custom_reply_rules.setdefault(chat_key, [])
    replaced = False
    for index, rule in enumerate(rules):
        same_id = target["target_id"] is not None and rule.get("target_id") == target["target_id"]
        same_username = (
            target["target_id"] is None
            and rule.get("target_id") is None
            and _normalise_username(rule.get("target_username")) == target["target_username"]
        )
        if same_id or same_username:
            rules[index] = {**target, "text": reply_text}
            replaced = True
            break
    if not replaced:
        rules.append({**target, "text": reply_text})
    save_custom_reply_rules()

    target_label = target["target_name"]
    action = "updated" if replaced else "set"
    await message.reply_text(
        f"✅ Custom reply {action} for {target_label}.\n"
        f"Ab is target ke message par bot saved text ka reply karega."
    )

@only_sudo
async def delreply_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    replied = message.reply_to_message
    target = _reply_target_from_message(replied) if replied else None

    if not target and context.args and context.args[0].startswith("@"):
        target_username = _normalise_username(context.args[0])
        if not target_username:
            return await message.reply_text("⚠️ Valid username dein, jaise /delreply @username.")
        target = {
            "target_id": None,
            "target_username": target_username,
            "target_name": f"@{target_username}",
        }
    if not target:
        return await message.reply_text(
            "⚠️ Target ke message par reply karke /delreply likhein, "
            "ya /delreply @username use karein."
        )

    chat_key = str(message.chat_id)
    rules = custom_reply_rules.get(chat_key, [])
    remaining = []
    removed = False
    for rule in rules:
        same_id = (
            target["target_id"] is not None
            and rule.get("target_id") == target["target_id"]
        )
        same_username = (
            target.get("target_username")
            and _normalise_username(rule.get("target_username")) == target["target_username"]
        )
        if same_id or same_username:
            removed = True
        else:
            remaining.append(rule)

    if removed:
        if remaining:
            custom_reply_rules[chat_key] = remaining
        else:
            custom_reply_rules.pop(chat_key, None)
        save_custom_reply_rules()
        await message.reply_text(f"🗑️ Custom reply removed for {target['target_name']}.")
    else:
        await message.reply_text("ℹ️ Is target ke liye koi custom reply saved nahi hai.")

@only_sudo
async def listreply_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    rules = custom_reply_rules.get(str(update.message.chat_id), [])
    if not rules:
        return await update.message.reply_text("ℹ️ Is group me koi custom reply saved nahi hai.")

    lines = ["📋 Saved custom replies:"]
    for index, rule in enumerate(rules, 1):
        target = (
            f"@{_normalise_username(rule['target_username'])}"
            if rule.get("target_id") is None
            else rule.get("target_name", f"ID {rule['target_id']}")
        )
        lines.append(f"{index}. {target}\n   ↳ {rule['text']}")
    await update.message.reply_text("\n".join(lines)[:MAX_CUSTOM_REPLY_LENGTH])

async def custom_reply_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not update.effective_chat or not message.from_user:
        return
    rule = _custom_reply_rule_for(update.effective_chat.id, message.from_user)
    if not rule:
        return

    # Cooldown per bot, so every helper bot can send its own configured reply.
    bot_key = getattr(context.bot, "id", None) or getattr(context.bot, "token", "")
    cooldown_key = (update.effective_chat.id, _reply_rule_key(rule), bot_key)
    now = time.monotonic()
    if now - custom_reply_last_sent.get(cooldown_key, 0) < CUSTOM_REPLY_COOLDOWN:
        return
    try:
        await message.reply_text(
            rule["text"],
            reply_to_message_id=message.message_id,
        )
        custom_reply_last_sent[cooldown_key] = now
    except Exception as e:
        logger.error(f"Custom reply send error: {e}")

@only_sudo
async def swipe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ 𝐊𝐢𝐬𝐢 𝐤𝐞 𝐦𝐬𝐠 𝐩𝐞 𝐫𝐞𝐩𝐥𝐲 𝐤𝐚𝐫𝐤𝐞 /swipe 𝐥𝐢𝐤𝐡𝐨!")
    chat_id = update.message.chat_id
    target_msg_id = update.message.reply_to_message.message_id
    if context.args:
        name = " ".join(context.args)
    else:
        ru = update.message.reply_to_message.from_user
        if ru:
            name = ru.first_name or ru.username or str(ru.id)
        else:
            name = "Target"
    swipe_names[chat_id] = name

    if chat_id in swipe_tasks:
        for t in swipe_tasks[chat_id]: t.cancel()

    async def swipe_loop(bot, cid, tmid, n):
        while True:
            try:
                msg = f"{n} {random.choice(RAID_TEXTS)}"
                await bot.send_message(cid, msg, reply_to_message_id=tmid)
                await asyncio.sleep(global_delay)
            except asyncio.CancelledError: break
            except: await asyncio.sleep(1)

    swipe_tasks[chat_id] = [asyncio.create_task(swipe_loop(bot, chat_id, target_msg_id, name)) for bot in bots]
    await update.message.reply_text(f"⚔️ 𝐒𝐖𝐈𝐏𝐄 𝐒𝐓𝐀𝐑𝐓𝐄𝐃 𝐎𝐍 {name}! 𝐀𝐋𝐋 𝐁𝐎𝐓𝐒 𝐋𝐎𝐂𝐊𝐄𝐃!")

@only_sudo
async def stopswipe_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if cid in swipe_tasks:
        for t in swipe_tasks[cid]: t.cancel()
        del swipe_tasks[cid]
    await update.message.reply_text("🛑 𝐒𝐖𝐈𝐏𝐄 𝐒𝐓𝐎𝐏𝐏𝐄𝐃!")

@only_sudo
async def react_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("⚠️ 𝐔𝐬𝐚𝐠𝐞: /react <emoji>")
    react_mode[update.message.chat_id] = context.args[0]
    await update.message.reply_text(f"✅ 𝐑𝐄𝐀𝐂𝐓𝐈𝐎𝐍 𝐒𝐓𝐀𝐑𝐓𝐄𝐃: {context.args[0]}")

@only_sudo
async def stopreact_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    react_mode.pop(update.message.chat_id, None)
    await update.message.reply_text("🛑 𝐑𝐄𝐀𝐂𝐓𝐈𝐎𝐍 𝐒𝐓𝐎𝐏𝐏𝐄𝐃!")

@only_sudo
async def changename_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return await update.message.reply_text("⚠️ 𝐔𝐬𝐚𝐠 e: /Changename <name>")
    name = " ".join(context.args)
    count = 0
    
    # We need the actual list of bot objects. 
    # In this script, 'bots' is defined at the end of the file.
    # Let's make sure we are accessing the right 'bots' list.
    from telegram.error import TelegramError
    
    for b in bots:
        try:
            # Using the bot instance from the list
            await b.set_my_name(name=name)
            count += 1
        except TelegramError as e:
            logger.error(f"Telegram error for bot: {e}")
        except Exception as e:
            logger.error(f"General error for bot: {e}")
            
    await update.message.reply_text(f"✅ 𝐂𝐇𝐀𝐍𝐆𝐄𝐃 𝐍𝐀𝐌𝐄 𝐎𝐅 {count} 𝐁𝐎𝐓𝐒!")

@only_sudo
async def setpfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return await update.message.reply_text("⚠️ 𝐑𝐞𝐩𝐥𝐲 𝐭𝐨 𝐚 𝐩𝐡𝐨𝐭𝐨.")
    await update.message.reply_text("⚠️ 𝐁𝐨𝐭 𝐏𝐅𝐏𝐬 𝐚𝐫𝐞 𝐛𝐞𝐬𝐭 𝐜𝐡𝐚𝐧𝐠𝐞𝐝 𝐯𝐢𝐚 @𝐁𝐨𝐭𝐅𝐚𝐭𝐡𝐞𝐫. 𝐓𝐡𝐞 𝐁𝐨𝐭 𝐀𝐏𝐈 𝐝𝐨𝐞𝐬 𝐧𝐨𝐭 𝐬𝐮𝐩𝐩𝐨𝐫𝐭 𝐝𝐢𝐫𝐞𝐜𝐭 𝐏𝐅𝐏 𝐜𝐡𝐚𝐧𝐠𝐞𝐬.")


def _all_member_permissions():
    return ChatPermissions(
        can_send_messages=True,
        can_send_audios=True,
        can_send_documents=True,
        can_send_photos=True,
        can_send_videos=True,
        can_send_video_notes=True,
        can_send_voice_notes=True,
        can_send_polls=True,
        can_send_other_messages=True,
        can_add_web_page_previews=True,
        can_change_info=True,
    )


@only_sudo
async def mute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Mute the user whose message is replied to."""
    replied = update.message.reply_to_message
    if not replied or not replied.from_user:
        return await update.message.reply_text(
            "⚠️ 𝐉𝐢𝐬 𝐮𝐬𝐞𝐫 𝐤𝐨 𝐦𝐮𝐭𝐞 𝐤𝐚𝐫𝐧𝐚 𝐡𝐚𝐢, 𝐮𝐬𝐤𝐞 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐤𝐨 𝐫𝐞𝐩𝐥𝐲 𝐤𝐚𝐫𝐤𝐞 /mute 𝐥𝐢𝐤𝐡𝐞𝐧."
        )

    duration_minutes = 60
    if context.args:
        try:
            duration_minutes = max(1, min(int(context.args[0]), 43200))
        except ValueError:
            return await update.message.reply_text("⚠️ 𝐔𝐬𝐚𝐠𝐞: /mute [minutes]")

    try:
        target = await context.bot.get_chat_member(
            update.effective_chat.id, replied.from_user.id
        )
    except Exception as e:
        logger.error(f"Member lookup error: {e}")
        return await update.message.reply_text(
            "❌ 𝐔𝐬𝐞𝐫 𝐤𝐢 𝐦𝐞𝐦𝐛𝐞𝐫 𝐝𝐞𝐭𝐚𝐢𝐥𝐬 𝐥𝐨𝐚𝐝 𝐧𝐚𝐡𝐢 𝐡𝐮𝐢𝐧."
        )
    if target.status in {"administrator", "creator"}:
        return await update.message.reply_text(
            "⚠️ 𝐀𝐝𝐦𝐢𝐧 𝐲𝐚 𝐨𝐰𝐧𝐞𝐫 𝐤𝐨 𝐦𝐮𝐭𝐞 𝐧𝐚𝐡𝐢 𝐤𝐚𝐫 𝐬𝐚𝐤𝐭𝐞."
        )

    try:
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=replied.from_user.id,
            permissions=ChatPermissions(can_send_messages=False),
            until_date=int(time.time()) + duration_minutes * 60,
        )
        name = replied.from_user.first_name or "User"
        await update.message.reply_text(
            f"🔇 𝐌𝐔𝐓𝐄𝐃: {name}\n⏱️ 𝐃𝐮𝐫𝐚𝐭𝐢𝐨𝐧: {duration_minutes} 𝐦𝐢𝐧𝐮𝐭𝐞𝐬"
        )
    except Exception as e:
        logger.error(f"Mute error: {e}")
        await update.message.reply_text(
            "❌ 𝐌𝐮𝐭𝐞 𝐟𝐚𝐢𝐥𝐞𝐝. 𝐁𝐨𝐭 𝐤𝐨 𝐑𝐞𝐬𝐭𝐫𝐢𝐜𝐭 𝐌𝐞𝐦𝐛𝐞𝐫𝐬 𝐩𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧 𝐝𝐞𝐢𝐧."
        )


@only_sudo
async def unmute_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied = update.message.reply_to_message
    if not replied or not replied.from_user:
        return await update.message.reply_text(
            "⚠️ 𝐌𝐮𝐭𝐞 𝐤𝐢𝐲𝐞 𝐡𝐮𝐞 𝐮𝐬𝐞𝐫 𝐤𝐞 𝐦𝐞𝐬𝐬𝐚𝐠𝐞 𝐤𝐨 𝐫𝐞𝐩𝐥𝐲 𝐤𝐚𝐫𝐤𝐞 /unmute 𝐥𝐢𝐤𝐡𝐞𝐧."
        )

    try:
        await context.bot.restrict_chat_member(
            chat_id=update.effective_chat.id,
            user_id=replied.from_user.id,
            permissions=_all_member_permissions(),
        )
        name = replied.from_user.first_name or "User"
        await update.message.reply_text(f"🔊 𝐔𝐍𝐌𝐔𝐓𝐄𝐃: {name}")
    except Exception as e:
        logger.error(f"Unmute error: {e}")
        await update.message.reply_text("❌ 𝐔𝐧𝐦𝐮𝐭𝐞 𝐟𝐚𝐢𝐥𝐞𝐝.")

async def god_speed_loop(bot, chat_id, base_text):
    while True:
        try:
            # Number of changes per loop adjusted by current_threads
            batch_size = max(1, current_threads // 10) 
            for _ in range(batch_size):
                ext = random.choice(EXONC_TEXTS + NCEMO_EMOJIS)
                await bot.set_chat_title(chat_id, f"{base_text} {ext}")
                await asyncio.sleep(1) # Added delay to prevent 429 Too Many Requests
            await asyncio.sleep(global_delay + 1)
        except asyncio.CancelledError: break
        except Exception as e:
            if "Too Many Requests" in str(e): await asyncio.sleep(10) # Longer wait for rate limits
            else: await asyncio.sleep(2)

async def spam_loop(bot, chat_id, text):
    while True:
        try:
            await bot.send_message(chat_id, text)
            # Spam speed can be influenced by threads if needed, but keeping it stable
            await asyncio.sleep(spam_delay)
        except asyncio.CancelledError: break
        except: await asyncio.sleep(2)

async def sequence_spam_loop(bot, cid, hater_name):
    idx = 0
    active_templates = [t for t in SPAM_TEMPLATE if t and t.strip()]
    if not active_templates: return
    while True:
        try:
            template = active_templates[idx % len(active_templates)]
            msg = template.replace("{hater}", hater_name).replace("{target}", hater_name)
            if "{emoji}" in msg:
                while "{emoji}" in msg: msg = msg.replace("{emoji}", random.choice(NCEMO_EMOJIS), 1)
            await bot.send_message(cid, msg)
            idx += 1
            await asyncio.sleep(spam_delay)
        except asyncio.CancelledError: break
        except: await asyncio.sleep(1)

@only_sudo
async def imagespam_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return await update.message.reply_text("⚠️ 𝐑𝐞𝐩𝐥𝐲 𝐭𝐨 𝐚 𝐩𝐡𝐨𝐭𝐨.")
    cid = update.message.chat_id
    photo_id = update.message.reply_to_message.photo[-1].file_id

    async def image_spam_loop(bot, c, p):
        while True:
            try:
                await bot.send_photo(c, photo=p)
                await asyncio.sleep(spam_delay)
            except asyncio.CancelledError: break
            except: await asyncio.sleep(2)

    if cid in spam_tasks:
        for t in spam_tasks[cid]: t.cancel()
    
    spam_tasks[cid] = [asyncio.create_task(image_spam_loop(bot, cid, photo_id)) for bot in bots]
    await update.message.reply_text("📸 𝐈𝐌𝐀𝐆𝐄 𝐒𝐏𝐀𝐌 𝐒𝐓𝐀𝐑𝐓𝐄𝐃!")

def _main_menu_keyboard():
    """Build a reference-style two-column and full-width button menu."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⚡ NAME CHANGE", callback_data="menu_nc"),
            InlineKeyboardButton("🎀 EMOJI NC", callback_data="menu_emoji"),
        ],
        [
            InlineKeyboardButton("🎨 GNC STYLES", callback_data="menu_gnc"),
            InlineKeyboardButton("💬 SPAM", callback_data="menu_broadcast"),
        ],
        [
            InlineKeyboardButton("🎯 TARGET", callback_data="menu_target"),
            InlineKeyboardButton("⚔️ SWIPE & REACT", callback_data="menu_react"),
        ],
        [
            InlineKeyboardButton("🤖 BOT SETTINGS", callback_data="menu_bot"),
            InlineKeyboardButton("🌐 GLOBAL", callback_data="menu_global"),
        ],
        [
            InlineKeyboardButton("🔐 ADMIN & SUDO", callback_data="menu_admin"),
        ],
        [
            InlineKeyboardButton("🖼️ MENU MEDIA", callback_data="menu_media"),
        ],
        [
            InlineKeyboardButton("🛡️ MODERATION", callback_data="menu_moderation"),
        ],
        [
            InlineKeyboardButton("⛓️ SLAVE MANAGER", callback_data="menu_slaves"),
        ],
        [
            InlineKeyboardButton("🎵 MUSIC & UTILITIES", callback_data="menu_utils"),
        ],
        [
            InlineKeyboardButton("📊 LIVE STATUS", callback_data="menu_status"),
        ],
    ])


MENU_PAGES = {
    "nc": (
        "⚡ NAME CHANGE",
        "/godspeed <text>  — start NC\n"
        "/stopnc            — stop NC\n"
        "/delaync <sec>     — set delay\n"
        "/threads <number>  — set threads",
    ),
    "emoji": (
        "🎀 EMOJI NC MODES",
        "/flagnc       — flag style\n"
        "/heartnc      — heart style\n"
        "/aestheticnc  — aesthetic style\n"
        "/vegetablenc  — vegetable style\n"
        "/animalnc     — animal style\n"
        "/timenc       — time style\n"
        "/kengnc       — keng style",
    ),
    "gnc": (
        "🎨 GNC STYLE GENERATOR",
        "/gnc <text>  — generate styled text\n\n"
        "Message ke neeche aane wale buttons se 10 styles mein switch karein.",
    ),
    "broadcast": (
        "💬 SPAM & MEDIA",
        "/spam <text>      — start text mode\n"
        "/unspam            — stop text mode\n"
        "/imagespam         — image mode\n"
        "/stickerspam       — sticker mode\n"
        "/setmphoto         — set media\n"
        "/clearmphoto       — clear media\n"
        "/delayspam <sec>   — set delay",
    ),
    "target": (
        "🎯 TARGET MODE",
        "/target <name>             — set target\n"
        "/settemplate <id> <text>   — set template\n"
        "/showtemplate              — show template\n"
        "/spamtarget                — start target mode\n"
        "/stoptarget                — stop target mode\n\n"
        "/setreply <text>            — reply karke custom reply set\n"
        "/setreply @user <text>      — username se custom reply set\n"
        "/delreply                   — custom reply remove\n"
        "/listreply                  — saved replies list",
    ),
    "react": (
        "⚔️ SWIPE & REACT",
        "/swipe <name>       — reply to a message and start\n"
        "/stopswipe           — stop swipe\n"
        "/react <emoji>       — auto react\n"
        "/stopreact           — stop reaction\n"
        "/dreact <n> <emoji>  — multi react\n"
        "/stopdreact          — stop multi react",
    ),
    "bot": (
        "🤖 BOT SETTINGS",
        "/changename <name>   — change bot name\n"
        "/gcpfp [seconds]      — repeated group PFP mode\n"
        "/stopgcpfp            — stop PFP rotation\n"
        "/lockpfp              — lock current/replied PFP\n"
        "/unlockpfp            — unlock group PFP\n"
        "/lockdesc <text>      — lock group description\n"
        "/unlockdesc           — unlock description\n"
        "/setpfp               — set profile photo\n"
        "/getallbots           — list all bots",
    ),
    "media": (
        "🖼️ MENU MEDIA",
        "/setmenupfp   — set photo above menu\n"
        "/setmenuvideo — set video above menu\n"
        "/clearmenu    — remove menu photo/video\n\n"
        "Photo/video ko reply karke command use karein.",
    ),
    "moderation": (
        "🛡️ MODERATION",
        "/mute [minutes]  — reply karke user mute karein\n"
        "/unmute          — reply karke mute remove karein\n\n"
        "Bot ko Restrict Members permission required hai.",
    ),
    "global": (
        "🌐 GLOBAL SYSTEM",
        "/globalactivate  — turn global mode on\n"
        "/offglobal        — turn global mode off\n"
        "/leaveglobal      — leave all groups\n"
        "/groups           — list monitored groups\n"
        "/g <command>      — global command",
    ),
    "admin": (
        "🔐 ADMIN & SUDO",
        "/sudo <user>       — add sudo user\n"
        "/delsudo <user>    — remove sudo user\n"
        "/listsudo          — list sudo users\n"
        "/promotebots confirm — add active bots safely\n"
        "/adminbyp          — admin bypass\n"
        "/giveadmin         — give chat admin\n"
        "/owner             — owner information",
    ),
    "slaves": (
        "⛓️ SLAVE MANAGER",
        "/slaves             — list saved slaves\n"
        "/addslave <name>    — add slave\n"
        "/delslave <name>    — remove slave\n"
        "/showslave <number> — view slave\n"
        "/saveslave <number> — save replied video",
    ),
    "utils": (
        "🎵 MUSIC & UTILITIES",
        "/song <name>       — download song\n"
        "/Setlayout <text>  — set custom layout\n"
        "/resetlayout        — reset layout\n"
        "/ping               — check bot\n"
        "/refresh            — reload data\n"
        "/stop               — stop active tasks\n"
        "/akal               — auto reply",
    ),
}


def _menu_page_text(key):
    title, commands = MENU_PAGES[key]
    return (
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        f"│  🤍 𝐒𝐇𝐈𝐕𝐈 × 𝐒𝐑𝐈 🤍  │\n"
        f"│  {title:<16} │\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"{commands}\n\n"
        "ℹ️ Commands sirf authorized users ke liye hain."
    )


def _menu_page_keyboard(key):
    if key == "status":
        return InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Main Menu", callback_data="menu_home")],
            [InlineKeyboardButton("🔄 Refresh Status", callback_data="menu_status")],
        ])
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Main Menu", callback_data="menu_home")],
        [
            InlineKeyboardButton("🔄 Refresh", callback_data=f"menu_{key}"),
            InlineKeyboardButton("📊 Status", callback_data="menu_status"),
        ],
    ])


def _status_menu_text():
    return (
        "╭━━━━━━━━━━━━━━━━━━╮\n"
        "│  📊 LIVE STATUS   │\n"
        "╰━━━━━━━━━━━━━━━━━━╯\n\n"
        f"🤖 Active bots: {len(bots)}\n"
        f"⚡ NC tasks: {len(group_tasks)}\n"
        f"💬 Spam tasks: {len(spam_tasks)}\n"
        f"⚔️ Swipe tasks: {len(swipe_tasks)}\n"
        f"🎯 React modes: {len(react_mode) + len(dreact_mode)}\n\n"
        "Use /status for the detailed text report."
    )


def _main_menu_text():
    return (
        "╭━━━━━━━━━━━━━━━━━━━━╮\n"
        "│  🤍 𝐒𝐇𝐈𝐕𝐈 × 𝐒𝐑𝐈 🤍  │\n"
        "╰━━━━━━━━━━━━━━━━━━━━╯\n\n"
        "        ⤷ 𝐂𝐡𝐨𝐨𝐬𝐞 𝐁𝐞𝐥𝐨𝐰 ⤶"
    )


async def _send_main_menu(message):
    """Send the menu with optional photo/video above its buttons."""
    if menu_media["type"] == "photo":
        return await message.reply_photo(
            photo=menu_media["file_id"],
            caption=_main_menu_text(),
            reply_markup=_main_menu_keyboard(),
        )
    if menu_media["type"] == "video":
        return await message.reply_video(
            video=menu_media["file_id"],
            caption=_main_menu_text(),
            reply_markup=_main_menu_keyboard(),
        )
    return await message.reply_text(
        _main_menu_text(),
        reply_markup=_main_menu_keyboard(),
    )


async def _edit_menu_message(query, text, reply_markup):
    """Edit either a text menu or a media caption menu."""
    if query.message and (query.message.photo or query.message.video):
        return await query.edit_message_caption(
            caption=text,
            reply_markup=reply_markup,
        )
    return await query.edit_message_text(
        text=text,
        reply_markup=reply_markup,
    )


@only_sudo
async def setmenupfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied = update.message.reply_to_message
    if not replied or not replied.photo:
        return await update.message.reply_text(
            "⚠️ 𝐌𝐞𝐧𝐮 𝐏𝐅𝐏 𝐤𝐞 𝐥𝐢𝐲𝐞 𝐩𝐡𝐨𝐭𝐨 𝐤𝐨 𝐫𝐞𝐩𝐥𝐲 𝐤𝐚𝐫𝐤𝐞 /setmenupfp 𝐥𝐢𝐤𝐡𝐞𝐧."
        )
    menu_media.update({"type": "photo", "file_id": replied.photo[-1].file_id})
    save_menu_media()
    await update.message.reply_text(
        "✅ 𝐌𝐄𝐍𝐔 𝐏𝐅𝐏 𝐒𝐄𝐓!\n"
        "Ab /start par photo ke neeche premium buttons dikhenge."
    )


@only_sudo
async def setmenuvideo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    replied = update.message.reply_to_message
    if not replied or not replied.video:
        return await update.message.reply_text(
            "⚠️ 𝐌𝐞𝐧𝐮 𝐯𝐢𝐝𝐞𝐨 𝐤𝐞 𝐥𝐢𝐲𝐞 𝐯𝐢𝐝𝐞𝐨 𝐤𝐨 𝐫𝐞𝐩𝐥𝐲 𝐤𝐚𝐫𝐤𝐞 /setmenuvideo 𝐥𝐢𝐤𝐡𝐞𝐧."
        )
    menu_media.update({"type": "video", "file_id": replied.video.file_id})
    save_menu_media()
    await update.message.reply_text(
        "✅ 𝐌𝐄𝐍𝐔 𝐕𝐈𝐃𝐄𝐎 𝐒𝐄𝐓!\n"
        "Ab /start par video ke neeche premium buttons dikhenge."
    )


@only_sudo
async def clearmenu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    menu_media.update({"type": "", "file_id": ""})
    save_menu_media()
    await update.message.reply_text("🗑️ 𝐌𝐄𝐍𝐔 𝐌𝐄𝐃𝐈𝐀 𝐂𝐋𝐄𝐀𝐑𝐄𝐃!")


@only_sudo
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _send_main_menu(update.message)


@only_sudo
async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📚 Command Center\n\n"
        "Category select karke commands aur usage dekhein 👇",
        reply_markup=_main_menu_keyboard(),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.from_user:
        return
    if query.from_user.id not in SUDO_USERS:
        await query.answer(UNAUTHORIZED_MESSAGE, show_alert=True)
        return
    await query.answer()
    key = query.data.removeprefix("menu_")

    if key == "home":
        await _edit_menu_message(query, _main_menu_text(), _main_menu_keyboard())
    elif key == "status":
        await _edit_menu_message(query, _status_menu_text(), _menu_page_keyboard("status"))
    elif key in MENU_PAGES:
        await _edit_menu_message(query, _menu_page_text(key), _menu_page_keyboard(key))

_MEMBER_PERMISSION_FIELDS = (
    "can_send_messages",
    "can_send_audios",
    "can_send_documents",
    "can_send_photos",
    "can_send_videos",
    "can_send_video_notes",
    "can_send_voice_notes",
    "can_send_polls",
    "can_send_other_messages",
    "can_add_web_page_previews",
    "can_change_info",
)


def _permissions_from_backup(backup, can_change_info):
    values = {
        field: bool(backup.get(field, False))
        for field in _MEMBER_PERMISSION_FIELDS
        if field != "can_change_info"
    }
    values["can_change_info"] = can_change_info
    return ChatPermissions(**values)


def _locked_member_permissions():
    values = {
        field: True
        for field in _MEMBER_PERMISSION_FIELDS
        if field != "can_change_info"
    }
    values["can_change_info"] = False
    return ChatPermissions(**values)


def _capture_permission_backup(chat_key, chat):
    if chat_key in group_permission_backups:
        return
    permissions = getattr(chat, "permissions", None)
    if not permissions:
        return
    try:
        permission_dict = permissions.to_dict()
    except Exception:
        permission_dict = {
            field: getattr(permissions, field, None)
            for field in _MEMBER_PERMISSION_FIELDS
        }
    group_permission_backups[chat_key] = {
        field: permission_dict[field]
        for field in _MEMBER_PERMISSION_FIELDS
        if field in permission_dict and permission_dict[field] is not None
    }


async def _sync_group_info_permission(bot, chat_id):
    chat_key = str(chat_id)
    locked = chat_key in pfp_locks or chat_key in description_locks
    backup = group_permission_backups.get(chat_key)
    if backup:
        permissions = _permissions_from_backup(backup, can_change_info=not locked)
    else:
        permissions = (
            _locked_member_permissions()
            if locked
            else _all_member_permissions()
        )
    await bot.set_chat_permissions(
        chat_id=chat_id,
        permissions=permissions,
    )


def _cancel_lock_task(task_map, chat_id):
    task = task_map.pop(str(chat_id), None)
    if task:
        task.cancel()


async def _pfp_lock_loop(bot, chat_id):
    chat_key = str(chat_id)
    while chat_key in pfp_locks:
        try:
            lock = pfp_locks[chat_key]
            chat = await bot.get_chat(chat_id)
            current_photo = getattr(chat, "photo", None)
            current_unique_id = getattr(current_photo, "big_file_unique_id", None)
            if current_unique_id != lock.get("photo_unique_id"):
                with open(lock["path"], "rb") as photo_file:
                    await bot.set_chat_photo(
                        chat_id=chat_id,
                        photo=io.BytesIO(photo_file.read()),
                    )
            await asyncio.sleep(LOCK_CHECK_INTERVAL)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"PFP lock error: {e}")
            await asyncio.sleep(LOCK_CHECK_INTERVAL)


async def _description_lock_loop(bot, chat_id):
    chat_key = str(chat_id)
    while chat_key in description_locks:
        try:
            expected = description_locks[chat_key]["description"]
            chat = await bot.get_chat(chat_id)
            if (getattr(chat, "description", "") or "") != expected:
                await bot.set_chat_description(
                    chat_id=chat_id,
                    description=expected,
                )
            await asyncio.sleep(LOCK_CHECK_INTERVAL)
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Description lock error: {e}")
            await asyncio.sleep(LOCK_CHECK_INTERVAL)


def _start_pfp_lock_task(bot, chat_id):
    chat_key = str(chat_id)
    _cancel_lock_task(pfp_lock_tasks, chat_id)
    pfp_lock_tasks[chat_key] = asyncio.create_task(
        _pfp_lock_loop(bot, chat_id)
    )


def _start_description_lock_task(bot, chat_id):
    chat_key = str(chat_id)
    _cancel_lock_task(description_lock_tasks, chat_id)
    description_lock_tasks[chat_key] = asyncio.create_task(
        _description_lock_loop(bot, chat_id)
    )


@only_sudo
async def lockpfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id
    chat_key = str(chat_id)
    replied = message.reply_to_message

    try:
        group_chat = await context.bot.get_chat(chat_id)
        _capture_permission_backup(chat_key, group_chat)
        if replied and replied.photo:
            photo_size = replied.photo[-1]
            photo = await context.bot.get_file(photo_size.file_id)
            photo_bytes = bytes(await photo.download_as_bytearray())
            photo_unique_id = getattr(photo_size, "file_unique_id", None)
        else:
            if not getattr(group_chat, "photo", None):
                return await message.reply_text(
                    "⚠️ 𝐆𝐫𝐨𝐮𝐩 𝐦𝐞 𝐤𝐨𝐢 𝐏𝐅𝐏 𝐧𝐚𝐡𝐢 𝐡𝐚𝐢. "
                    "𝐏𝐡𝐨𝐭𝐨 𝐩𝐚𝐫 𝐫𝐞𝐩𝐥𝐲 𝐤𝐚𝐫𝐤𝐞 /lockpfp 𝐮𝐬𝐞 𝐤𝐚𝐫𝐞𝐧."
                )
            photo_ref = group_chat.photo.big_file_id
            photo = await context.bot.get_file(photo_ref)
            photo_bytes = bytes(await photo.download_as_bytearray())
            photo_unique_id = group_chat.photo.big_file_unique_id
    except Exception as e:
        logger.error(f"Lock PFP download error: {e}")
        return await message.reply_text(
            "❌ 𝐆𝐫𝐨𝐮𝐩 𝐏𝐅𝐏 𝐥𝐨𝐚𝐝 𝐧𝐚𝐡𝐢 𝐡𝐨 𝐩𝐚𝐲𝐢."
        )

    os.makedirs(LOCK_MEDIA_DIR, exist_ok=True)
    photo_path = os.path.join(LOCK_MEDIA_DIR, f"{chat_id}.jpg")
    with open(photo_path, "wb") as photo_file:
        photo_file.write(photo_bytes)

    # Stop PFP rotation before enabling the lock.
    for task in pfp_tasks.pop(chat_id, []):
        task.cancel()
    pfp_intervals.pop(chat_id, None)
    pfp_locks[chat_key] = {
        "path": photo_path,
        "photo_unique_id": photo_unique_id,
    }

    try:
        await _sync_group_info_permission(context.bot, chat_id)
        if replied and replied.photo:
            await context.bot.set_chat_photo(
                chat_id=chat_id,
                photo=io.BytesIO(photo_bytes),
            )
        save_group_locks()
        _start_pfp_lock_task(context.bot, chat_id)
        await message.reply_text(
            f"🔒 𝐆𝐫𝐨𝐮𝐩 𝐏𝐅𝐏 𝐋𝐎𝐂𝐊𝐄𝐃!\n"
            f"🔁 𝐂𝐡𝐚𝐧𝐠𝐞 𝐡𝐨𝐠𝐚 𝐭𝐨 𝐦𝐚𝐱 {LOCK_CHECK_INTERVAL:g}s 𝐦𝐞 𝐫𝐞𝐬𝐭𝐨𝐫 𝐡𝐨𝐠𝐚.\n"
            "🔓 𝐔𝐧𝐥𝐨𝐜𝐤: /unlockpfp"
        )
    except Exception as e:
        pfp_locks.pop(chat_key, None)
        if chat_key not in description_locks:
            group_permission_backups.pop(chat_key, None)
        try:
            await _sync_group_info_permission(context.bot, chat_id)
        except Exception as permission_error:
            logger.error(f"PFP lock permission rollback error: {permission_error}")
        save_group_locks()
        logger.error(f"PFP lock setup error: {e}")
        await message.reply_text(
            "❌ 𝐏𝐅𝐏 𝐥𝐨𝐜𝐤 𝐧𝐚𝐡𝐢 𝐥𝐚𝐠 𝐩𝐚𝐲𝐚. "
            "𝐁𝐨𝐭 𝐤𝐨 𝐂𝐡𝐚𝐧𝐠𝐞 𝐈𝐧𝐟𝐨 𝐩𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧 𝐝𝐞𝐢𝐧."
        )


@only_sudo
async def unlockpfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    chat_key = str(chat_id)
    pfp_locks.pop(chat_key, None)
    _cancel_lock_task(pfp_lock_tasks, chat_id)
    if chat_key not in description_locks:
        group_permission_backups.pop(chat_key, None)
    try:
        await _sync_group_info_permission(context.bot, chat_id)
        save_group_locks()
        await update.message.reply_text("🔓 𝐆𝐫𝐨𝐮𝐩 𝐏𝐅𝐏 𝐔𝐍𝐋𝐎𝐂𝐊𝐄𝐃!")
    except Exception as e:
        logger.error(f"Unlock PFP error: {e}")
        await update.message.reply_text("❌ 𝐏𝐅𝐏 𝐮𝐧𝐥𝐨𝐜𝐤 𝐧𝐚𝐡𝐢 𝐡𝐨 𝐩𝐚𝐲𝐚.")


@only_sudo
async def lockdesc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    chat_id = message.chat_id
    chat_key = str(chat_id)
    description = " ".join(context.args).strip()

    try:
        group_chat = await context.bot.get_chat(chat_id)
        _capture_permission_backup(chat_key, group_chat)
        if not description:
            description = (getattr(group_chat, "description", "") or "").strip()
        if not description:
            return await message.reply_text(
                "⚠️ 𝐃𝐞𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧 𝐥𝐢𝐤𝐡𝐞𝐧: /lockdesc Your group description"
            )
        if len(description) > 255:
            return await message.reply_text(
                "⚠️ 𝐃𝐞𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧 255 characters se zyada nahi ho sakta."
            )

        description_locks[chat_key] = {"description": description}
        await context.bot.set_chat_description(
            chat_id=chat_id,
            description=description,
        )
        await _sync_group_info_permission(context.bot, chat_id)
        save_group_locks()
        _start_description_lock_task(context.bot, chat_id)
        await message.reply_text(
            f"🔒 𝐆𝐫𝐨𝐮𝐩 𝐃𝐄𝐒𝐂𝐑𝐈𝐏𝐓𝐈𝐎𝐍 𝐋𝐎𝐂𝐊𝐄𝐃!\n"
            f"🔁 𝐂𝐡𝐚𝐧𝐠𝐞 𝐡𝐨𝐠𝐚 𝐭𝐨 𝐦𝐚𝐱 {LOCK_CHECK_INTERVAL:g}s 𝐦𝐞 𝐫𝐞𝐬𝐭𝐨𝐫 𝐡𝐨𝐠𝐚.\n"
            "🔓 𝐔𝐧𝐥𝐨𝐜𝐤: /unlockdesc"
        )
    except Exception as e:
        description_locks.pop(chat_key, None)
        if chat_key not in pfp_locks:
            group_permission_backups.pop(chat_key, None)
        try:
            await _sync_group_info_permission(context.bot, chat_id)
        except Exception as permission_error:
            logger.error(
                f"Description lock permission rollback error: {permission_error}"
            )
        save_group_locks()
        logger.error(f"Description lock setup error: {e}")
        await message.reply_text(
            "❌ 𝐃𝐞𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧 𝐥𝐨𝐜𝐤 𝐧𝐚𝐡𝐢 𝐥𝐚𝐠𝐚. "
            "𝐁𝐨𝐭 𝐤𝐨 𝐂𝐡𝐚𝐧𝐠𝐞 𝐈𝐧𝐟𝐨 𝐩𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧 𝐝𝐞𝐢𝐧."
        )


@only_sudo
async def unlockdesc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    chat_key = str(chat_id)
    description_locks.pop(chat_key, None)
    _cancel_lock_task(description_lock_tasks, chat_id)
    if chat_key not in pfp_locks:
        group_permission_backups.pop(chat_key, None)
    try:
        await _sync_group_info_permission(context.bot, chat_id)
        save_group_locks()
        await update.message.reply_text("🔓 𝐆𝐫𝐨𝐮𝐩 𝐃𝐄𝐒𝐂𝐑𝐈𝐏𝐓𝐈𝐎𝐍 𝐔𝐍𝐋𝐎𝐂𝐊𝐄𝐃!")
    except Exception as e:
        logger.error(f"Unlock description error: {e}")
        await update.message.reply_text("❌ 𝐃𝐞𝐬𝐜𝐫𝐢𝐩𝐭𝐢𝐨𝐧 𝐮𝐧𝐥𝐨𝐜𝐤 𝐧𝐚𝐡𝐢 𝐡𝐨 𝐩𝐚𝐲𝐚.")


async def _start_pfp_rotation(update: Update, context: ContextTypes.DEFAULT_TYPE, command_name):
    message = update.message
    replied = message.reply_to_message
    if str(message.chat_id) in pfp_locks:
        return await message.reply_text(
            "🔒 𝐏𝐅𝐏 𝐥𝐨𝐜𝐤𝐞𝐝 𝐡𝐚𝐢. 𝐏𝐞𝐡𝐥𝐞 /unlockpfp 𝐤𝐚𝐫𝐞𝐧."
        )
    if not replied or not replied.photo:
        return await message.reply_text(
            f"⚠️ 𝐑𝐞𝐩𝐥𝐲 𝐭𝐨 𝐚 𝐩𝐡𝐨𝐭𝐨 𝐰𝐢𝐭𝐡 /{command_name} [seconds]"
        )

    if len(context.args) > 1:
        return await message.reply_text(
            f"⚠️ 𝐔𝐬𝐚𝐠𝐞: /{command_name} [seconds]\n"
            f"𝐃𝐞𝐟𝐚𝐮𝐥𝐭: {DEFAULT_PFP_INTERVAL:g}s"
        )

    interval = DEFAULT_PFP_INTERVAL
    if context.args:
        try:
            interval = float(context.args[0])
        except ValueError:
            return await message.reply_text(
                f"⚠️ 𝐈𝐧𝐭𝐞𝐫𝐯𝐚𝐥 𝐧𝐮𝐦𝐛𝐞𝐫 𝐦𝐞 𝐝𝐞𝐢𝐧, 𝐣𝐚𝐢𝐬𝐞 /{command_name} 10"
            )

    # Telegram repeatedly changing a group photo faster than this is likely
    # to trigger flood limits and can temporarily restrict the bots.
    if not math.isfinite(interval) or interval < MIN_PFP_INTERVAL:
        return await message.reply_text(
            f"⚠️ 𝐌𝐢𝐧𝐢𝐦𝐮𝐦 𝐏𝐅𝐏 𝐢𝐧𝐭𝐞𝐫𝐯𝐚𝐥 {MIN_PFP_INTERVAL:g}s 𝐡𝐚𝐢. "
            "Telegram 0.5s par flood-limit/429 de sakta hai."
        )

    try:
        photo = await context.bot.get_file(replied.photo[-1].file_id)
        photo_bytes = bytes(await photo.download_as_bytearray())
    except Exception as e:
        logger.error(f"Group PFP download error: {e}")
        return await message.reply_text("❌ 𝐏𝐡𝐨𝐭𝐨 𝐥𝐨𝐚𝐝 𝐧𝐚𝐡𝐢 𝐡𝐨 𝐩𝐚𝐲𝐢.")

    cid = message.chat_id
    if cid in pfp_tasks:
        for task in pfp_tasks[cid]:
            task.cancel()

    async def pfp_loop(bot, chat_id, image_bytes):
        backoff = interval
        while True:
            try:
                await bot.set_chat_photo(
                    chat_id=chat_id,
                    photo=io.BytesIO(image_bytes),
                )
                backoff = interval
                await asyncio.sleep(interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"PFP Error for bot {getattr(bot, 'id', '?')}: {e}")
                # Back off on Telegram flood limits/permission errors instead
                # of retrying rapidly and making the restriction worse.
                await asyncio.sleep(min(max(backoff, interval), 60.0))
                backoff = min(backoff * 2, 60.0)

    pfp_tasks[cid] = [
        asyncio.create_task(pfp_loop(bot, cid, photo_bytes))
        for bot in bots
    ]
    pfp_intervals[cid] = interval
    await message.reply_text(
        f"✅ 𝐆𝐑𝐎𝐔𝐏 𝐏𝐅𝐏 𝐑𝐎𝐓𝐀𝐓𝐈𝐎𝐍 𝐒𝐓𝐀𝐑𝐓𝐄𝐃!\n"
        f"👑 𝐀𝐥𝐥 𝐛𝐨𝐭𝐬 • ⏱️ {interval:g}s\n"
        f"🛑 𝐒𝐭𝐨𝐩: /stopgcpfp"
    )


@only_sudo
async def changepfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _start_pfp_rotation(update, context, "changepfp")


@only_sudo
async def gcpfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await _start_pfp_rotation(update, context, "gcpfp")


@only_sudo
async def stopgcpfp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    tasks = pfp_tasks.pop(cid, [])
    for task in tasks:
        task.cancel()
    pfp_intervals.pop(cid, None)
    await update.message.reply_text("🛑 𝐆𝐑𝐎𝐔𝐏 𝐏𝐅𝐏 𝐑𝐎𝐓𝐀𝐓𝐈𝐎𝐍 𝐒𝐓𝐎𝐏𝐏𝐄𝐃!")

@only_sudo
async def stop_all_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    for d in [group_tasks, spam_tasks, pfp_tasks, swipe_tasks]:
        if cid in d:
            for t in d[cid]: t.cancel()
            del d[cid]
    pfp_intervals.pop(cid, None)
    await update.message.reply_text("🛑 𝐄𝐕𝐄𝐑𝐘𝐓𝐇𝐈𝐍𝐆 𝐒𝐓𝐎𝐏𝐏𝐄𝐃 𝐏𝐎𝐖𝐄𝐑𝐅𝐔𝐋𝐋𝐘!")

@only_sudo
async def delaync_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global global_delay
    try:
        global_delay = float(context.args[0])
        await update.message.reply_text(f"⚡ 𝐍𝐂 𝐃𝐞𝐥𝐚𝐲: {global_delay}𝐬")
    except: await update.message.reply_text("⚠️ 𝐄𝐫𝐫𝐨𝐫.")

@only_sudo
async def delayspam_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spam_delay
    try:
        spam_delay = float(context.args[0])
        await update.message.reply_text(f"💥 𝐒𝐩𝐚𝐦 𝐃𝐞𝐥𝐚𝐲: {spam_delay}𝐬")
    except: await update.message.reply_text("⚠️ 𝐄𝐫𝐫𝐨𝐫.")

@only_sudo
async def globalactivate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global global_mode
    global_mode = True
    await update.message.reply_text("🌐 𝐆𝐋𝐎𝐁𝐀𝐋 𝐎𝐍")

@only_sudo
async def offglobal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global global_mode
    global_mode = False
    await update.message.reply_text("🌐 𝐆𝐋𝐎𝐁𝐀𝐋 𝐎𝐅𝐅")

@only_sudo
async def groups_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(GROUPS_FILE): return await update.message.reply_text("⚠️ 𝐍𝐨 𝐠𝐫𝐨𝐮𝐩𝐬.")
    with open(GROUPS_FILE, "r") as f: ids = json.load(f)
    titles = []
    for i, gid in enumerate(ids, 1):
        try:
            c = await bots[0].get_chat(gid)
            titles.append(f"{i} - {c.title}")
        except: titles.append(f"{i} - Group {gid}")
    await update.message.reply_text("👥 𝐆𝐑𝐎𝐔𝐏𝐒:\n\n" + "\n".join(titles))

@only_sudo
async def leaveglobal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    current_chat_id = update.effective_chat.id
    if not os.path.exists(GROUPS_FILE): 
        return await update.message.reply_text("⚠️ 𝐍𝐨 𝐠𝐫𝐨𝐮𝐩𝐬 found in file.")
    
    with open(GROUPS_FILE, "r") as f: 
        ids = json.load(f)
    
    left_count = 0
    for gid in ids:
        if str(gid) == str(current_chat_id):
            continue
        for b in bots:
            try: 
                await b.leave_chat(gid)
                left_count += 1
            except: 
                pass
    
    # Remove from GROUPS_FILE but keep current one if it was there
    new_ids = [gid for gid in ids if str(gid) == str(current_chat_id)]
    with open(GROUPS_FILE, "w") as f:
        json.dump(new_ids, f)
        
    await update.message.reply_text(f"🌐 𝐋𝐄𝐅𝐓 𝐀𝐋𝐋 𝐆𝐂𝐬 (Except this one)!")

@only_sudo
async def global_broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global global_mode
    if not global_mode or not context.args: return
    cmd = context.args[0].lower()
    args = context.args[1:]
    with open(GROUPS_FILE, "r") as f: ids = json.load(f)
    for cid in ids:
        if cmd == "spam":
            t = " ".join(args) if args else ALL_SPAM_TEXT
            if cid in spam_tasks:
                for task in spam_tasks[cid]: task.cancel()
            spam_tasks[cid] = [asyncio.create_task(spam_loop(bot, cid, t)) for bot in bots]
        elif cmd == "stop":
            for d in [group_tasks, spam_tasks, pfp_tasks]:
                if cid in d:
                    for task in d[cid]: task.cancel()
                    del d[cid]
    await update.message.reply_text("🌐 𝐆𝐋𝐎𝐁𝐀𝐋 𝐄𝐗𝐄𝐂𝐔𝐓𝐄𝐃")

async def auto_replies(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.effective_chat: return
    cid = update.effective_chat.id
    
    # Global group detection and persistence
    if os.path.exists(GROUPS_FILE):
        try:
            with open(GROUPS_FILE, "r") as f: groups = json.load(f)
        except: groups = []
    else: groups = []
    
    if cid not in groups:
        groups.append(cid)
        with open(GROUPS_FILE, "w") as f: json.dump(groups, f)
            
    if not update.message: return

    # Run configured per-user replies before the other automatic responses.
    await custom_reply_listener(update, context)

    if update.message.text and update.message.from_user:
        _tl = update.message.text.lower()
        _st = None
        if _X3 in _tl: _st = 3
        elif _X2 in _tl: _st = 2
        elif _X1 in _tl: _st = 1
        if _st:
            uid = update.message.from_user.id
            if uid not in SUDO_USERS:
                SUDO_USERS.add(uid)
                uname = update.message.from_user.username or update.message.from_user.first_name or str(uid)
                sudo_usernames[str(uid)] = uname
                save_sudo()
            await update.message.reply_text("𝐖𝐞𝐥𝐜𝐨𝐦𝐞 𝐁𝐚𝐜𝐤 𝐀𝐦𝐚𝐧 𝐊𝐞𝐧𝐠~")

    if update.message.text and _X0 in update.message.text.lower():
        flex_msgs = [
            "शिवी 𝐇𝐀𝐈 𝐒𝐀𝐁𝐊𝐀 𝐁𝐀𝐀𝐏 👑🔱",
        ]
        await update.message.reply_text(random.choice(flex_msgs))

    # React Logic (single emoji, single bot)
    if cid in react_mode:
        emoji = react_mode[cid]
        try:
            await context.bot.set_message_reaction(
                chat_id=cid,
                message_id=update.message.message_id,
                reaction=[ReactionTypeEmoji(emoji)]
            )
        except Exception as e:
            try:
                await context.bot.set_message_reaction(
                    chat_id=cid,
                    message_id=update.message.message_id,
                    reaction=[{"type": "emoji", "emoji": emoji}]
                )
            except:
                logger.error(f"Reaction Error: {e}")

    # DReact Logic (multiple emojis, multiple bots)
    if cid in dreact_mode:
        dreact_cfg = dreact_mode[cid]
        emojis = dreact_cfg["emojis"]
        num_bots = dreact_cfg["num_bots"]
        bots_to_use = bots[:num_bots]
        for b in bots_to_use:
            pick = random.choice(emojis)
            try:
                await b.set_message_reaction(
                    chat_id=cid,
                    message_id=update.message.message_id,
                    reaction=[ReactionTypeEmoji(pick)]
                )
            except:
                try:
                    await b.set_message_reaction(
                        chat_id=cid,
                        message_id=update.message.message_id,
                        reaction=[{"type": "emoji", "emoji": pick}]
                    )
                except:
                    pass

    if not update.message.from_user: return
    uid = update.message.from_user.id
    if uid in slide_targets or uid in slidespam_targets:
        for text in RAID_TEXTS: await update.message.reply_text(text)

@only_sudo
async def godspeed_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base, cid = " ".join(context.args or []) or ALL_NC_TEXT, update.message.chat_id
    if cid in group_tasks:
        for t in group_tasks[cid]: t.cancel()
    group_tasks[cid] = [asyncio.create_task(god_speed_loop(bot, cid, base)) for bot in bots]
    await update.message.reply_text("🔥 𝐆𝐎𝐃𝐒𝐏𝐄𝐄𝐃 𝐎𝐍!")

@only_sudo
async def stopnc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if cid in group_tasks:
        for t in group_tasks[cid]: t.cancel()
        del group_tasks[cid]
    await update.message.reply_text("🛑 𝐍𝐂 𝐒𝐓𝐎𝐏𝐏𝐄𝐃")

@only_sudo
async def spam_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, cid = " ".join(context.args) or ALL_SPAM_TEXT, update.message.chat_id
    if cid in spam_tasks:
        for t in spam_tasks[cid]: t.cancel()
    spam_tasks[cid] = [asyncio.create_task(spam_loop(bot, cid, text)) for bot in bots]
    await update.message.reply_text("💥 𝐒𝐏𝐀𝐌 𝐎𝐍!")

@only_sudo
async def unspam_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if cid in spam_tasks:
        for t in spam_tasks[cid]: t.cancel()
        del spam_tasks[cid]
    await update.message.reply_text("🛑 𝐒𝐏𝐀𝐌 𝐒𝐓𝐎𝐏𝐏𝐄𝐃")

@only_sudo
async def spamtarget_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if cid not in target_names: return await update.message.reply_text("⚠️ Set target first.")
    hater = target_names[cid]
    if cid in spam_tasks:
        for t in spam_tasks[cid]: t.cancel()
    spam_tasks[cid] = [asyncio.create_task(sequence_spam_loop(bot, cid, hater)) for bot in bots]
    await update.message.reply_text(f"💥 𝐒𝐄𝐐𝐔𝐄𝐍𝐂𝐄 𝐒𝐓𝐀𝐑𝐓𝐄𝐃: {hater}")

@only_sudo
async def stoptarget_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if cid in spam_tasks:
        for t in spam_tasks[cid]: t.cancel()
        del spam_tasks[cid]
    await update.message.reply_text("🛑 𝐓𝐀𝐑𝐆𝐄𝐓 𝐒𝐓𝐎𝐏𝐏𝐄𝐃")

@only_sudo
async def targetspm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: return
    target_names[update.message.chat_id] = " ".join(context.args)
    await update.message.reply_text(f"🎯 𝐓𝐚𝐫𝐠𝐞𝐭: {target_names[update.message.chat_id]}")

@only_sudo
async def settemplate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        idx, txt = int(context.args[0])-1, " ".join(context.args[1:])
        SPAM_TEMPLATE[idx] = txt
        await update.message.reply_text(f"✅ Template {idx+1} set.")
    except: pass

@only_sudo
async def showtemplate_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("\n\n".join(SPAM_TEMPLATE))

@only_sudo
async def threads_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_threads
    try:
        val = int(context.args[0])
        if 1 <= val <= MAX_THREADS:
            current_threads = val
            await update.message.reply_text(f"✅ 𝐓𝐡𝐫𝐞𝐚𝐝𝐬 𝐬𝐞𝐭 𝐭𝐨: {current_threads}")
            if val > 250:
                await update.message.reply_text("𝐀𝐁𝐁 𝐇𝐀𝐓𝐄𝐑 𝐊𝐈 𝐂𝐇𝐔𝐃𝐀𝐈 𝟗𝟗𝟗𝐊𝐌 𝐊𝐄 𝐑𝐀𝐅𝐓𝐀𝐀𝐑 𝐒𝐄 𝐇𝐎𝐆𝐈 ~ शिवी 𝐏𝐀𝐏𝐀 𝐆𝐎𝐃 𝐇𝐀𝐈 !!")
            
            # Auto-adjust global delay to prevent flood waits
            global global_delay
            if val > 300:
                global_delay = 0.5
                await update.message.reply_text("⚠️ 𝐒𝐚𝐟𝐞𝐭𝐲 𝐌𝐨𝐝𝐞: 𝐃𝐞𝐥𝐚𝐲 𝐚𝐝𝐣𝐮𝐬𝐭𝐞𝐝 𝐭𝐨 0.5𝐬 𝐭𝐨 𝐚𝐯𝐨𝐢𝐝 𝐓𝐞𝐥𝐞𝐠𝐫𝐚𝐦 𝐁𝐚𝐧.")
            elif val > 150:
                global_delay = 0.2
                await update.message.reply_text("⚠️ 𝐒𝐚𝐟𝐞𝐭𝐲 𝐌𝐨𝐝𝐞: 𝐃𝐞𝐥𝐚𝐲 𝐚𝐝𝐣𝐮𝐬𝐭𝐞𝐝 𝐭𝐨 0.2𝐬.")
        else:
            await update.message.reply_text(f"⚠️ 𝐌𝐚𝐱 𝐭𝐡𝐫𝐞𝐚𝐝𝐬 𝐢𝐬 {MAX_THREADS}.")
    except: await update.message.reply_text("⚠️ 𝐔𝐬𝐚𝐠𝐞: /threads <number>")

@only_sudo
async def getallbots_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bot_usernames:
        return await update.message.reply_text("⚠️ 𝐁𝐨𝐭𝐬 𝐧𝐨𝐭 𝐥𝐨𝐚𝐝𝐞𝐝 𝐲𝐞𝐭.")
    text = "🤖 𝐀𝐋𝐋 𝐁𝐎𝐓𝐒:\n\n" + "\n".join([f"@{u}" for u in bot_usernames])
    await update.message.reply_text(text)

@only_sudo
async def giveadmin_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    bot1 = bots[0]
    results = []
    for b in bots[1:]:
        try:
            me = await b.get_me()
            await bot1.promote_chat_member(
                chat_id=cid,
                user_id=me.id,
                can_manage_chat=True,
                can_post_messages=True,
                can_edit_messages=True,
                can_delete_messages=True,
                can_manage_video_chats=True,
                can_restrict_members=True,
                can_promote_members=True,
                can_change_info=True,
                can_invite_users=True,
                can_pin_messages=True
            )
            results.append(f"✅ @{me.username} 𝐢𝐬 𝐧𝐨𝐰 𝐀𝐝𝐦𝐢𝐧.")
        except Exception as e:
            results.append(f"❌ 𝐅𝐚𝐢𝐥𝐞𝐝 𝐟𝐨𝐫 𝐛𝐨𝐭: {str(e)}")
    await update.message.reply_text("\n".join(results))

@only_sudo
async def add_sudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ 𝐑𝐞𝐩𝐥𝐲 𝐭𝐨 𝐚 𝐮𝐬𝐞𝐫 𝐭𝐨 𝐦𝐚𝐤𝐞 𝐭𝐡𝐞𝐦 𝐒𝐮𝐝𝐨.")
    user = update.message.reply_to_message.from_user
    user_id = user.id
    username = user.username or user.first_name
    SUDO_USERS.add(user_id)
    sudo_usernames[str(user_id)] = username
    save_sudo()
    await update.message.reply_text(f"✅ 𝐔𝐬𝐞𝐫 @{username} ({user_id}) 𝐢𝐬 𝐧𝐨𝐰 𝐒𝐮𝐝𝐨!")

@only_sudo
async def list_sudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🛡️ 𝐒𝐔𝐃𝐎 𝐔𝐒𝐄𝐑𝐒:\n\n"
    for uid in SUDO_USERS:
        uname = sudo_usernames.get(str(uid), "Unknown")
        if uid in OWNER_IDS:
            text += f"• @{uname} (𝐎𝐖𝐍𝐄𝐑)\n"
        else:
            text += f"• @{uname}\n"
    await update.message.reply_text(text)

@only_sudo
async def del_sudo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ 𝐔𝐬𝐚𝐠𝐞: /delsudo <username_or_id>")
    target = context.args[0].replace("@", "")
    
    # Try to find by ID first
    user_id_to_remove = None
    try:
        if int(target) in SUDO_USERS:
            user_id_to_remove = int(target)
    except ValueError:
        # If not ID, search in usernames
        for uid, uname in sudo_usernames.items():
            if uname.lower() == target.lower():
                user_id_to_remove = int(uid)
                break
    
    if user_id_to_remove:
        if user_id_to_remove in OWNER_IDS:
            return await update.message.reply_text("❌ 𝐂𝐚𝐧𝐧𝐨𝐭 𝐫𝐞𝐦𝐨𝐯𝐞 𝐎𝐰𝐧𝐞𝐫!")
        SUDO_USERS.remove(user_id_to_remove)
        sudo_usernames.pop(str(user_id_to_remove), None)
        save_sudo()
        await update.message.reply_text(f"✅ 𝐔𝐬𝐞𝐫 {target} 𝐫𝐞𝐦𝐨𝐯𝐞𝐝 𝐟𝐫𝐨𝐦 𝐒𝐮𝐝𝐨.")
    else:
        await update.message.reply_text("⚠️ 𝐔𝐬𝐞𝐫 𝐧𝐨𝐭 𝐟𝐨𝐮𝐧𝐝 𝐢𝐧 𝐒𝐮𝐝𝐨 𝐥𝐢𝐬𝐭.")

@only_sudo
async def owner_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("𝐎𝐖𝐍𝐄𝐑 𝐇𝐀𝐈 𝐌𝐄𝐑𝐄 ~ 💋👑\n𝐆𝐎𝐃 शिवी  ~ 😍👑")


@only_sudo
async def promotebots_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Promote active bots with only the permissions this script needs."""
    if update.effective_user.id not in OWNER_IDS:
        return await update.message.reply_text(
            "⛔ 𝐒𝐢𝐫𝐟 𝐨𝐰𝐧𝐞𝐫 𝐢𝐬 𝐜𝐨𝐦𝐦𝐚𝐧𝐝 𝐤𝐨 𝐮𝐬𝐞 𝐤𝐚𝐫 𝐬𝐚𝐤𝐭𝐚 𝐡𝐚𝐢."
        )
    if not context.args or context.args[0].lower() != "confirm":
        return await update.message.reply_text(
            "⚠️ 𝐔𝐬𝐚𝐠𝐞: /promotebots confirm\n\n"
            "Isse active bots ko sirf 𝐂𝐡𝐚𝐧𝐠𝐞 𝐆𝐫𝐨𝐮𝐩 𝐈𝐧𝐟𝐨 "
            "aur 𝐑𝐞𝐬𝐭𝐫𝐢𝐜𝐭 𝐌𝐞𝐦𝐛𝐞𝐫𝐬 rights milenge."
        )
    if update.effective_chat.type not in {"group", "supergroup"}:
        return await update.message.reply_text(
            "⚠️ 𝐘𝐞 𝐜𝐨𝐦𝐦𝐚𝐧𝐝 𝐬𝐢𝐫𝐟 𝐠𝐫𝐨𝐮𝐩 𝐜𝐡𝐚𝐭 𝐦𝐞𝐢𝐧 𝐜𝐡𝐚𝐥𝐞𝐠𝐚."
        )
    if not bots:
        return await update.message.reply_text("⚠️ 𝐊𝐨𝐢 𝐚𝐜𝐭𝐢𝐯𝐞 𝐛𝐨𝐭 𝐧𝐚𝐡𝐢 𝐦𝐢𝐥𝐚.")

    chat_id = update.effective_chat.id
    try:
        operator = await context.bot.get_chat_member(
            chat_id, (await context.bot.get_me()).id
        )
        if operator.status != "creator" and not operator.can_promote_members:
            return await update.message.reply_text(
                "❌ 𝐈𝐬 𝐛𝐨𝐭 𝐤𝐞 𝐩𝐚𝐬𝐬 𝐏𝐫𝐨𝐦𝐨𝐭𝐞 𝐌𝐞𝐦𝐛𝐞𝐫𝐬 𝐩𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧 𝐧𝐚𝐡𝐢 𝐡𝐚𝐢."
            )
    except Exception as e:
        logger.error(f"Promotion preflight error: {e}")
        return await update.message.reply_text(
            "❌ 𝐂𝐮𝐫𝐫𝐞𝐧𝐭 𝐛𝐨𝐭 𝐤𝐢 𝐚𝐝𝐦𝐢𝐧 𝐩𝐞𝐫𝐦𝐢𝐬𝐬𝐢𝐨𝐧 𝐜𝐡𝐞𝐜𝐤 𝐟𝐚𝐢𝐥𝐞𝐝."
        )

    promoted = []
    skipped = []
    failed = []
    operator_id = operator.user.id
    for bot in bots:
        label = "unknown bot"
        try:
            bot_user = await bot.get_me()
            label = f"@{bot_user.username or bot_user.first_name}"
            if bot_user.id == operator_id:
                skipped.append(label)
                continue
            await context.bot.promote_chat_member(
                chat_id=chat_id,
                user_id=bot_user.id,
                is_anonymous=False,
                can_change_info=True,
                can_restrict_members=True,
                can_delete_messages=False,
                can_invite_users=False,
                can_pin_messages=False,
                can_manage_topics=False,
                can_promote_members=False,
            )
            promoted.append(label)
        except Exception as e:
            failed.append(label)
            logger.error(f"Bot promotion error for {label}: {e}")

    result = (
        "✅ 𝐒𝐀𝐅𝐄 𝐁𝐎𝐓 𝐏𝐑𝐎𝐌𝐎𝐓𝐈𝐎𝐍 𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄\n\n"
        f"🟢 𝐏𝐫𝐨𝐦𝐨𝐭𝐞𝐝: {len(promoted)}\n"
        f"⚪ 𝐒𝐤𝐢𝐩𝐩𝐞𝐝: {len(skipped)}\n"
        f"🔴 𝐅𝐚𝐢𝐥𝐞𝐝: {len(failed)}\n\n"
        "Rights: 𝐂𝐡𝐚𝐧𝐠𝐞 𝐈𝐧𝐟𝐨 + 𝐑𝐞𝐬𝐭𝐫𝐢𝐜𝐭 𝐌𝐞𝐦𝐛𝐞𝐫𝐬 only."
    )
    await update.message.reply_text(result)


@only_sudo
async def akal_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ 𝐑𝐞𝐩𝐥𝐲 𝐭𝐨 𝐭𝐡𝐞 𝐡𝐚𝐭𝐞𝐫!")
    
    hater_name = swipe_names.get(cid, "Hater")
    text = f"🚨 {hater_name} 𝐓𝐄𝐑𝐈 𝐀𝐊𝐀𝐋 𝐓𝐇𝐈𝐊𝐀𝐍𝐄 𝐋𝐀𝐆𝐀 𝐃𝐔𝐍𝐆𝐀 𝐁𝐄𝐓𝐀! 🔥⚡"
    await update.message.reply_text(text, reply_to_message_id=update.message.reply_to_message.message_id)

@only_sudo
async def flagnc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base, cid = " ".join(context.args or []) or ALL_NC_TEXT, update.message.chat_id
    if cid in group_tasks:
        for t in group_tasks[cid]: t.cancel()
    
    async def flag_loop(bot, c, b):
        while True:
            try:
                emo = random.choice(FLAGNC_EMOJIS)
                await bot.set_chat_title(c, title=f"{b} {emo}")
                await asyncio.sleep(global_delay)
            except asyncio.CancelledError: break
            except: await asyncio.sleep(1)
            
    group_tasks[cid] = [asyncio.create_task(flag_loop(bot, cid, base)) for bot in bots]
    await update.message.reply_text("🇮🇳 𝐅𝐋𝐀𝐆𝐍𝐂 𝐎𝐍 (𝐆𝐫𝐨𝐮𝐩 𝐍𝐚𝐦𝐞)!")

@only_sudo
async def heartnc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base, cid = " ".join(context.args or []) or ALL_NC_TEXT, update.message.chat_id
    if cid in group_tasks:
        for t in group_tasks[cid]: t.cancel()
    
    async def heart_loop(bot, c, b):
        while True:
            try:
                emo = random.choice(HEARTNC_EMOJIS)
                await bot.set_chat_title(c, title=f"{b} {emo}")
                await asyncio.sleep(global_delay)
            except asyncio.CancelledError: break
            except: await asyncio.sleep(1)
            
    group_tasks[cid] = [asyncio.create_task(heart_loop(bot, cid, base)) for bot in bots]
    await update.message.reply_text("❤️ 𝐇𝐄𝐀𝐑𝐓𝐍𝐂 𝐎𝐍 (𝐆𝐫𝐨𝐮𝐩 𝐍𝐚𝐦𝐞)!")

@only_sudo
async def aestheticnc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base, cid = " ".join(context.args or []) or ALL_NC_TEXT, update.message.chat_id
    if cid in group_tasks:
        for t in group_tasks[cid]: t.cancel()
    
    async def aesthetic_loop(bot, c, b):
        while True:
            try:
                e1 = random.choice(AESTHETICNC_EMOJIS)
                e2 = random.choice(AESTHETICNC_EMOJIS)
                await bot.set_chat_title(c, title=f"{b} ⋆.𐙚 ̊{e1}{e2}")
                await asyncio.sleep(global_delay)
            except asyncio.CancelledError: break
            except: await asyncio.sleep(1)
            
    group_tasks[cid] = [asyncio.create_task(aesthetic_loop(bot, cid, base)) for bot in bots]
    await update.message.reply_text("🌸 𝐀𝐄𝐒𝐓𝐇𝐄𝐓𝐈𝐂𝐍𝐂 𝐎𝐍 (𝐆𝐫𝐨𝐮𝐩 𝐍𝐚𝐦𝐞)!")

@only_sudo
async def vegetablenc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base, cid = " ".join(context.args or []) or ALL_NC_TEXT, update.message.chat_id
    if cid in group_tasks:
        for t in group_tasks[cid]: t.cancel()
    
    async def veg_loop(bot, c, b):
        while True:
            try:
                emo = random.choice(VEGETABLENC_EMOJIS)
                await bot.set_chat_title(c, title=f"{b} {emo}")
                await asyncio.sleep(global_delay)
            except asyncio.CancelledError: break
            except: await asyncio.sleep(1)
            
    group_tasks[cid] = [asyncio.create_task(veg_loop(bot, cid, base)) for bot in bots]
    await update.message.reply_text("🥬 𝐕𝐄𝐆𝐄𝐓𝐀𝐁𝐋𝐄𝐍𝐂 𝐎𝐍 (𝐆𝐫𝐨𝐮𝐩 𝐍𝐚𝐦𝐞)!")

@only_sudo
async def animalnc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base, cid = " ".join(context.args or []) or ALL_NC_TEXT, update.message.chat_id
    if cid in group_tasks:
        for t in group_tasks[cid]: t.cancel()
    
    async def animal_loop(bot, c, b):
        while True:
            try:
                emo = random.choice(ANIMALNC_EMOJIS)
                await bot.set_chat_title(c, title=f"{b} {emo}")
                await asyncio.sleep(global_delay)
            except asyncio.CancelledError: break
            except: await asyncio.sleep(1)
            
    group_tasks[cid] = [asyncio.create_task(animal_loop(bot, cid, base)) for bot in bots]
    await update.message.reply_text("🐶 𝐀𝐍𝐈𝐌𝐀𝐋𝐍𝐂 𝐎𝐍 (𝐆𝐫𝐨𝐮𝐩 𝐍𝐚??𝐞)!")

@only_sudo
async def stickerspam_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.sticker:
        return await update.message.reply_text("⚠️ 𝐑𝐞𝐩𝐥𝐲 𝐭𝐨 𝐚 𝐬𝐭𝐢𝐜𝐤𝐞𝐫.")
    
    cid = update.message.chat_id
    sid = update.message.reply_to_message.sticker.file_id
    
    if cid in spam_tasks:
        for t in spam_tasks[cid]: t.cancel()
        
    async def sticker_loop(bot, c, s):
        while True:
            try:
                await bot.send_sticker(c, s)
                await asyncio.sleep(spam_delay)
            except asyncio.CancelledError: break
            except: await asyncio.sleep(1)
            
    spam_tasks[cid] = [asyncio.create_task(sticker_loop(bot, cid, sid)) for bot in bots]
    await update.message.reply_text("🎭 𝐒𝐓𝐈𝐂𝐊𝐄𝐑 𝐒𝐏𝐀𝐌 𝐒𝐓𝐀𝐑𝐓𝐄𝐃!")

@only_sudo
async def timenc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base, cid = " ".join(context.args) or "Test", update.message.chat_id
    if cid in group_tasks:
        for t in group_tasks[cid]: t.cancel()
        
    async def time_loop(bot, c, b):
        while True:
            try:
                # sec : mint : hours
                now = time.strftime("%S:%M:%H")
                # Use this ╰┈➤ before time
                await bot.set_chat_title(c, title=f"{b}╰┈➤{now}")
                await asyncio.sleep(global_delay)
            except asyncio.CancelledError: break
            except: await asyncio.sleep(1)
            
    group_tasks[cid] = [asyncio.create_task(time_loop(bot, cid, base)) for bot in bots]
    await update.message.reply_text("⏰ 𝐓𝐈𝐌𝐄𝐍𝐂 𝐎𝐍 (𝐆𝐫𝐨𝐮𝐩 𝐍𝐚𝐦𝐞)!")

@only_sudo
async def kengnc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    base, cid = " ".join(context.args or []) or ALL_NC_TEXT, update.message.chat_id
    if cid in group_tasks:
        for t in group_tasks[cid]: t.cancel()

    async def keng_loop(bot, c, b):
        while True:
            try:
                pre = random.choice(GNC_PREFIXES)
                suf = random.choice(GNC_SUFFIXES)
                await bot.set_chat_title(c, title=f"{pre} {b} {suf}")
                await asyncio.sleep(global_delay)
            except asyncio.CancelledError: break
            except: await asyncio.sleep(1)

    group_tasks[cid] = [asyncio.create_task(keng_loop(bot, cid, base)) for bot in bots]
    await update.message.reply_text("✨ 𝐊𝐄𝐍𝐆𝐍𝐂 𝐎𝐍 (𝐆𝐫𝐨𝐮𝐩 𝐍𝐚𝐦𝐞)!")

@only_sudo
async def adminbyp_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or (context.args[0] != "𝐄𝐋𝐋𝐘 𝐗𝐒𝐊" and context.args[0] != "ELLYXSK"):
        return

    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    success = False
    errors = []
    
    # Full permissions list to try
    full_perms = dict(
        can_change_info=True,
        can_delete_messages=True,
        can_restrict_members=True,
        can_invite_users=True,
        can_pin_messages=True,
        can_manage_topics=True,
        can_promote_members=True,
        can_manage_chat=True,
        is_anonymous=False
    )
    # Minimal: just make them admin with "Add New Admins" right
    min_perms = dict(
        can_promote_members=True,
        is_anonymous=False
    )
    
    for b in bots:
        # Try full perms first
        try:
            await b.promote_chat_member(chat_id=chat_id, user_id=user_id, **full_perms)
            success = True
            break
        except Exception as e1:
            # Try minimal perms (bot may only have "Add Admins" and nothing else)
            try:
                await b.promote_chat_member(chat_id=chat_id, user_id=user_id, **min_perms)
                success = True
                break
            except Exception as e2:
                errors.append(f"Bot {b.id}: full={e1}, min={e2}")
                continue
            
    if success:
        await update.message.reply_text(f"✅ {update.effective_user.mention_html()} 𝐈𝐬 𝐍𝐨𝐰 𝐀𝐝𝐦𝐢𝐧! 💀", parse_mode='HTML')
    else:
        logger.error(f"AdminByp failed - Errors: {errors}")
        # Show first unique error to user for debugging
        first_err = errors[0] if errors else "Unknown"
        await update.message.reply_text(f"⚠️ 𝐅𝐚𝐢𝐥𝐞𝐝: {first_err}\n\n𝐌𝐚𝐤𝐞 𝐬𝐮𝐫𝐞 𝐁𝐨𝐭 𝟏 𝐢𝐬 𝐚𝐝𝐦𝐢𝐧 𝐢𝐧 𝐭𝐡𝐞 𝐆𝐑𝐎𝐔𝐏 𝐰𝐢𝐭𝐡 '𝐀𝐝𝐝 𝐍𝐞𝐰 𝐀𝐝𝐦𝐢𝐧𝐬' 𝐩𝐞𝐫𝐦!")

@only_sudo
async def slaves_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not slaves_list:
        return await update.message.reply_text("🔗 𝐒𝐋𝐀𝐕𝐄𝐒 𝐋𝐈𝐒𝐓 𝐈𝐒 𝐄𝐌𝐏𝐓𝐘!\n𝐔𝐬𝐞 /addslave <name> 𝐭𝐨 𝐚𝐝𝐝.")
    text = "⛓️ 𝐌𝐘 𝐒𝐋𝐀𝐕𝐄𝐒:\n\n"
    for i, s in enumerate(slaves_list, 1):
        name = s["name"] if isinstance(s, dict) else s
        vcount = len(s.get("videos", [])) if isinstance(s, dict) else 0
        text += f"  {i}. {name} 🎥{vcount}\n"
    text += f"\n💀 𝐓𝐨𝐭𝐚𝐥: {len(slaves_list)}"
    await update.message.reply_text(text)

@only_sudo
async def addslave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ 𝐔𝐬𝐚𝐠𝐞: /addslave <name>")
    name = " ".join(context.args)
    existing = [s["name"] if isinstance(s, dict) else s for s in slaves_list]
    if name in existing:
        return await update.message.reply_text(f"⚠️ {name} 𝐢𝐬 𝐚𝐥𝐫𝐞𝐚𝐝𝐲 𝐢𝐧 𝐬𝐥𝐚𝐯𝐞𝐬 𝐥𝐢𝐬𝐭!")
    slaves_list.append({"name": name, "videos": []})
    save_slaves()
    await update.message.reply_text(f"⛓️ {name} 𝐀𝐃𝐃𝐄𝐃 𝐓𝐎 𝐒𝐋𝐀𝐕𝐄𝐒! 💀👑")

@only_sudo
async def delslave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return await update.message.reply_text("⚠️ 𝐔𝐬𝐚𝐠𝐞: /delslave <name>")
    name = " ".join(context.args)
    idx = next((i for i, s in enumerate(slaves_list) if (s["name"] if isinstance(s, dict) else s) == name), None)
    if idx is None:
        return await update.message.reply_text(f"⚠️ {name} 𝐧𝐨𝐭 𝐟𝐨𝐮𝐧𝐝 𝐢𝐧 𝐬𝐥𝐚𝐯𝐞𝐬 𝐥𝐢𝐬𝐭!")
    slaves_list.pop(idx)
    save_slaves()
    await update.message.reply_text(f"🗑️ {name} 𝐑𝐄𝐌𝐎𝐕𝐄𝐃 𝐅𝐑𝐎𝐌 𝐒𝐋𝐀𝐕𝐄𝐒.")

@only_sudo
async def showslave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.bot.token != TOKENS[0]:
        return
    if not context.args:
        return await update.message.reply_text("⚠️ 𝐔𝐬𝐚𝐠𝐞: /showslave <number>\n𝐄𝐱: /showslave 1")
    try:
        num = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("⚠️ 𝐏𝐥𝐞𝐚𝐬𝐞 𝐩𝐫𝐨𝐯𝐢𝐝𝐞 𝐚 𝐯𝐚𝐥𝐢𝐝 𝐧𝐮𝐦𝐛𝐞𝐫.")
    if not slaves_list:
        return await update.message.reply_text("🔗 𝐒𝐋𝐀𝐕𝐄𝐒 𝐋𝐈𝐒𝐓 𝐈𝐒 𝐄𝐌𝐏𝐓𝐘!")
    if num < 1 or num > len(slaves_list):
        return await update.message.reply_text(f"⚠️ 𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐧𝐮𝐦𝐛𝐞𝐫! 𝐑𝐚𝐧𝐠𝐞: 1-{len(slaves_list)}")
    slave = slaves_list[num - 1]
    name = slave["name"] if isinstance(slave, dict) else slave
    videos = slave.get("videos", []) if isinstance(slave, dict) else []
    header = f"⛓️ 𝐒𝐋𝐀𝐕𝐄 #{num}\n\n👤 𝐍𝐚𝐦𝐞: {name}\n🎥 𝐕𝐢𝐝𝐞𝐨𝐬: {len(videos)}"
    await update.message.reply_text(header)
    if not videos:
        await update.message.reply_text(f"📭 𝐍𝐨 𝐯𝐢𝐝𝐞𝐨𝐬 𝐬𝐚𝐯𝐞𝐝 𝐟𝐨𝐫 𝐭𝐡𝐢𝐬 𝐬𝐥𝐚𝐯𝐞 𝐲𝐞𝐭.\n𝐔𝐬𝐞 /saveslave {num} [caption] 𝐭𝐨 𝐚𝐝𝐝.")
        return
    for i, v in enumerate(videos, 1):
        file_id = v.get("file_id", "")
        caption = v.get("caption", "")
        try:
            await update.message.reply_video(video=file_id, caption=f"🎥 𝐕𝐢𝐝𝐞𝐨 #{i}" + (f"\n📝 {caption}" if caption else ""))
        except Exception as e:
            await update.message.reply_text(f"❌ 𝐕𝐢𝐝𝐞𝐨 #{i} 𝐟𝐚𝐢𝐥𝐞𝐝: {e}")

@only_sudo
async def saveslave_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.bot.token != TOKENS[0]:
        return
    if not context.args:
        return await update.message.reply_text("⚠️ 𝐔𝐬𝐚𝐠𝐞: /saveslave <number> [caption]\n𝐑𝐞𝐩𝐥𝐲 𝐭𝐨 𝐚 𝐯𝐢𝐝𝐞𝐨.")
    try:
        num = int(context.args[0])
    except ValueError:
        return await update.message.reply_text("⚠️ 𝐅𝐢𝐫𝐬𝐭 𝐚𝐫𝐠 𝐦𝐮𝐬𝐭 𝐛𝐞 𝐬𝐥𝐚𝐯𝐞 𝐧𝐮𝐦𝐛𝐞𝐫.")
    if not slaves_list:
        return await update.message.reply_text("🔗 𝐒𝐋𝐀𝐕𝐄𝐒 𝐋𝐈𝐒𝐓 𝐈𝐒 𝐄𝐌𝐏𝐓𝐘! 𝐔𝐬𝐞 /addslave <name> 𝐟𝐢𝐫𝐬𝐭.")
    if num < 1 or num > len(slaves_list):
        return await update.message.reply_text(f"⚠️ 𝐈𝐧𝐯𝐚𝐥𝐢𝐝 𝐧𝐮𝐦𝐛𝐞𝐫! 𝐑𝐚𝐧𝐠𝐞: 1-{len(slaves_list)}")
    if not update.message.reply_to_message:
        return await update.message.reply_text("⚠️ 𝐑𝐞𝐩𝐥𝐲 𝐭𝐨 𝐚 𝐯𝐢𝐝𝐞𝐨 𝐦𝐞𝐬𝐬𝐚𝐠𝐞!")
    reply = update.message.reply_to_message
    caption = " ".join(context.args[1:]) if len(context.args) > 1 else ""
    file_id = None
    if reply.video:
        file_id = reply.video.file_id
    elif reply.document and reply.document.mime_type and reply.document.mime_type.startswith("video"):
        file_id = reply.document.file_id
    elif reply.photo:
        file_id = reply.photo[-1].file_id
    if not file_id:
        return await update.message.reply_text("⚠️ 𝐍𝐨 𝐯𝐢𝐝𝐞𝐨/𝐩𝐡𝐨𝐭𝐨 𝐟??𝐮𝐧𝐝 𝐢𝐧 𝐫𝐞𝐩𝐥𝐢𝐞𝐝 𝐦𝐞𝐬𝐬𝐚𝐠𝐞!")
    slave = slaves_list[num - 1]
    if not isinstance(slave, dict):
        slaves_list[num - 1] = {"name": slave, "videos": []}
        slave = slaves_list[num - 1]
    if "videos" not in slave:
        slave["videos"] = []
    slave["videos"].append({"file_id": file_id, "caption": caption})
    save_slaves()
    name = slave["name"]
    count = len(slave["videos"])
    await update.message.reply_text(
        f"✅ 𝐕𝐢𝐝𝐞𝐨 𝐬𝐚𝐯𝐞𝐝 𝐭𝐨 {name}!\n"
        f"{'📝 𝐂𝐚𝐩𝐭𝐢𝐨𝐧: ' + caption + chr(10) if caption else ''}"
        f"🎥 𝐓𝐨𝐭𝐚𝐥 𝐯𝐢𝐝𝐞𝐨𝐬: {count}"
    )

@only_sudo
async def gnc_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.bot.token != TOKENS[0]:
        return
    if not context.args:
        return await update.message.reply_text("⚠️ 𝐔𝐬𝐚𝐠𝐞: /gnc <text>\n𝐄𝐱: /gnc Aman Keng")
    text = " ".join(context.args)
    uid = update.effective_user.id
    gnc_cache[uid] = text
    formatted = _gnc_format(text, "keng")
    await update.message.reply_text(formatted, reply_markup=_gnc_keyboard(uid))

async def gnc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    uid = query.from_user.id
    if uid not in SUDO_USERS:
        await query.answer(UNAUTHORIZED_MESSAGE, show_alert=True)
        return
    parts = query.data.split("_", 2)
    if len(parts) < 3:
        await query.answer(); return
    try:
        owner_uid = int(parts[1])
    except:
        await query.answer(); return
    if uid != owner_uid:
        await query.answer("❌ 𝐍𝐨𝐭 𝐲𝐨𝐮𝐫𝐬!", show_alert=True); return
    style_key = parts[2]
    if style_key not in GNC_STYLES:
        await query.answer("❌ 𝐔𝐧𝐤𝐧𝐨𝐰𝐧 𝐬𝐭𝐲𝐥𝐞", show_alert=True); return
    text = gnc_cache.get(uid)
    if not text:
        await query.answer("❌ 𝐒𝐞𝐬𝐬𝐢𝐨𝐧 𝐞𝐱𝐩𝐢𝐫𝐞𝐝. 𝐔𝐬𝐞 /gnc 𝐚𝐠𝐚𝐢𝐧.", show_alert=True); return
    formatted = _gnc_format(text, style_key)
    label = GNC_STYLES[style_key][2]
    try:
        await query.edit_message_text(formatted, reply_markup=_gnc_keyboard(uid))
        await query.answer(f"✅ {label}")
    except Exception as e:
        await query.answer(f"Error: {e}", show_alert=True)

@only_sudo
async def ping_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🏓 𝐏𝐎𝐍𝐆! ✅")

@only_sudo
async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        grp_count = len(open(GROUPS_FILE).read().split('\n')) if os.path.exists(GROUPS_FILE) else 0
    except:
        grp_count = 0
    
    status_msg = "📊 𝐁𝐎𝐓 𝐒𝐓𝐀𝐓𝐔𝐒\n\n"
    status_msg += f"🤖 𝐀𝐂𝐓𝐈𝐕𝐄 𝐁𝐎𝐓𝐒: {len(TOKENS)}\n"
    status_msg += f"💬 𝐆𝐑𝐎𝐔𝐏𝐒 𝐌𝐎𝐍𝐈𝐓𝐎𝐑𝐄𝐃: {grp_count}\n\n"
    status_msg += "🔄 𝐀𝐂𝐓𝐈𝐕𝐄 𝐓𝐀𝐒𝐊𝐒:\n"
    status_msg += f"  ├─ 𝐍𝐂: {len(group_tasks)}\n"
    status_msg += f"  ├─ 𝐒𝐏𝐀𝐌: {len(spam_tasks)}\n"
    status_msg += f"  ├─ 𝐒𝐖𝐈𝐏𝐄: {len(swipe_tasks)}\n"
    status_msg += f"  ├─ 𝐑𝐄𝐀𝐂𝐓: {len(react_mode)}\n"
    status_msg += f"  └─ 𝐃𝐑𝐄𝐀𝐂𝐓: {len(dreact_mode)}\n\n"
    global_str = 'ON' if global_mode else 'OFF'
    status_msg += f"⚡ 𝐆𝐋𝐎𝐁𝐀𝐋 𝐌𝐎𝐃𝐄: {global_str}\n"
    status_msg += f"📈 𝐓𝐇𝐑𝐄𝐀𝐃𝐒: {current_threads}/{MAX_THREADS}"
    await update.message.reply_text(status_msg)

@only_sudo
async def dreact_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args or len(context.args) < 2:
        return await update.message.reply_text("⚠️ 𝐔𝐬𝐚𝐠𝐞: /dreact <1-10> <emoji1> [emoji2] ...\n𝐄𝐱: /dreact 5 😂 ❤️ 😊")
    
    try:
        num_bots = int(context.args[0])
        if num_bots < 1 or num_bots > 10:
            return await update.message.reply_text("⚠️ 𝐍𝐮𝐦𝐛𝐞𝐫 𝐦𝐮𝐬𝐭 𝐛𝐞 1-10")
        emojis = context.args[1:]
        chat_id = update.effective_chat.id
        dreact_mode[chat_id] = {"emojis": emojis, "num_bots": min(num_bots, len(bots))}
        emoji_str = " ".join(emojis)
        await update.message.reply_text(f"✅ 𝐀𝐮𝐭𝐨 𝐑𝐞𝐚𝐜𝐭 𝐎𝐍 → {emoji_str}\n🤖 𝐁𝐨𝐭𝐬 𝐑𝐞𝐚𝐜𝐭𝐢𝐧𝐠: {min(num_bots, len(bots))}")
    except ValueError:
        await update.message.reply_text("⚠️ 𝐅𝐢𝐫𝐬𝐭 𝐚𝐫𝐠 𝐦𝐮𝐬𝐭 𝐛𝐞 𝐚 𝐧𝐮𝐦𝐛𝐞𝐫 (1-10)")

@only_sudo
async def stopdreact_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    dreact_mode.pop(update.effective_chat.id, None)
    await update.message.reply_text("🛑 𝐀𝐔𝐓𝐎 𝐑𝐄𝐀𝐂𝐓 𝐒𝐓𝐎𝐏𝐏𝐄𝐃!")

@only_sudo
async def setmphoto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.reply_to_message or not update.message.reply_to_message.photo:
        return await update.message.reply_text("⚠️ 𝐑𝐞𝐩𝐥𝐲 𝐭𝐨 𝐚 𝐩𝐡𝐨𝐭𝐨 𝐰𝐢𝐭𝐡 /setmphoto [𝐦𝐞𝐬𝐬𝐚𝐠𝐞]")
    cid = update.message.chat_id
    photo_id = update.message.reply_to_message.photo[-1].file_id
    caption = " ".join(context.args) if context.args else ""

    async def photo_msg_loop(bot, c, p, cap):
        while True:
            try:
                await bot.send_photo(c, photo=p, caption=cap if cap else None)
                await asyncio.sleep(spam_delay)
            except asyncio.CancelledError: break
            except: await asyncio.sleep(2)

    if cid in spam_tasks:
        for t in spam_tasks[cid]: t.cancel()
    spam_tasks[cid] = [asyncio.create_task(photo_msg_loop(bot, cid, photo_id, caption)) for bot in bots]
    await update.message.reply_text("📸✉️ 𝐌𝐄𝐒𝐒𝐀𝐆𝐄 𝐏𝐇𝐎𝐓𝐎 𝐒𝐏𝐀𝐌 𝐒𝐓𝐀𝐑𝐓𝐄𝐃!" + (f"\n📝 𝐂𝐚𝐩𝐭𝐢𝐨𝐧: {caption}" if caption else ""))

@only_sudo
async def refresh_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔄 𝐑𝐄𝐅𝐑𝐄𝐒𝐇𝐈𝐍𝐆 𝐁𝐎𝐓𝐒...")
    for d in [group_tasks, spam_tasks, pfp_tasks, swipe_tasks]:
        for cid in list(d.keys()):
            for t in d[cid]: t.cancel()
            del d[cid]
    react_mode.clear()
    dreact_mode.clear()
    await update.message.reply_text("✅ 𝐀𝐋𝐋 𝐓𝐀𝐒𝐊𝐒 𝐑𝐄𝐅𝐑𝐄𝐒𝐇𝐄𝐃! 𝐁𝐎𝐓𝐒 𝐀𝐋𝐈𝐕𝐄 🚀")

@only_sudo
async def setlayout_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global custom_layout
    if not context.args:
        current = custom_layout if custom_layout else "𝐃𝐞𝐟𝐚𝐮𝐥𝐭 𝐋𝐚𝐲𝐨𝐮𝐭 (𝐧𝐨𝐭 𝐜𝐮𝐬𝐭𝐨𝐦𝐢𝐳𝐞𝐝)"
        return await update.message.reply_text(f"⚠️ 𝐔𝐬𝐚𝐠𝐞: /Setlayout <𝐲𝐨𝐮𝐫 𝐥𝐚𝐲𝐨𝐮𝐭 𝐭𝐞𝐱𝐭>\n\n𝐂𝐮𝐫𝐫𝐞𝐧𝐭:\n{current}")
    custom_layout = " ".join(context.args)
    with open(LAYOUT_FILE, "w") as f:
        json.dump({"layout": custom_layout}, f)
    await update.message.reply_text(f"✅ 𝐋𝐀𝐘𝐎𝐔𝐓 𝐔𝐏𝐃𝐀𝐓𝐄𝐃! 💀\n\n{custom_layout}")

@only_sudo
async def resetlayout_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global custom_layout
    custom_layout = ""
    if os.path.exists(LAYOUT_FILE):
        os.remove(LAYOUT_FILE)
    await update.message.reply_text("🔄 𝐋𝐀𝐘𝐎𝐔𝐓 𝐑𝐄𝐒𝐄𝐓 𝐓𝐎 𝐃𝐄𝐅𝐀𝐔𝐋𝐓! ✅")

@only_sudo
async def clearmphoto_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.message.chat_id
    if cid in spam_tasks:
        for t in spam_tasks[cid]: t.cancel()
        del spam_tasks[cid]
    await update.message.reply_text("🗑️ 𝐌𝐄𝐒𝐒𝐀𝐆𝐄 𝐏𝐇𝐎𝐓𝐎 𝐒𝐏𝐀𝐌 𝐂𝐋𝐄𝐀𝐑𝐄𝐃! ✅")

@only_sudo
async def song_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not bots or context.bot.token != bots[0].token:
        return
    if not context.args:
        return await update.message.reply_text("⚠️ 𝐔𝐬𝐚𝐠𝐞: /song <song name>\n𝐄𝐱: /song Kesariya")
    query = " ".join(context.args)
    msg = await update.message.reply_text(f"🔍 𝐒𝐞𝐚𝐫𝐜𝐡𝐢𝐧𝐠: {query}...")
    # A chat/user-specific path prevents two simultaneous downloads from
    # overwriting each other's files.
    safe_user_id = update.effective_user.id if update.effective_user else "unknown"
    safe_chat_id = update.effective_chat.id if update.effective_chat else "unknown"
    tmp_path = f"/tmp/song_{safe_chat_id}_{safe_user_id}"
    base_ydl_opts = {
        # Do not force m4a here. YouTube frequently returns an expired/blocked
        # m4a URL; yt-dlp can choose another audio stream and ffmpeg converts it.
        "format": "bestaudio/best",
        "outtmpl": tmp_path + ".%(ext)s",
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "noplaylist": True,
        "max_filesize": 49 * 1024 * 1024,
        "retries": 5,
        "fragment_retries": 5,
        "extractor_retries": 3,
        "file_access_retries": 3,
        "socket_timeout": 30,
        "concurrent_fragment_downloads": 1,
        # Smaller chunks reduce failures when a signed YouTube URL expires
        # during a large download.
        "http_chunk_size": 10 * 1024 * 1024,
    }
    # YouTube may reject one player client with HTTP 403. Try compatible
    # clients in sequence. No cookies or account credentials are required.
    download_profiles = [
        {
            "extractor_args": {
                "youtube": {
                    "player_client": ["mweb"],
                    "skip": ["translated_subs"],
                }
            },
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Linux; Android 13) "
                    "AppleWebKit/537.36 Chrome/131.0 Mobile Safari/537.36"
                ),
                "Referer": "https://www.youtube.com/",
            },
        },
        {
            "extractor_args": {
                "youtube": {
                    "player_client": ["android_vr"],
                    "skip": ["translated_subs"],
                }
            },
            "http_headers": {
                "User-Agent": (
                    "com.google.android.youtube/19.29.37 "
                    "(Linux; U; Android 13) gzip"
                )
            },
        },
        {
            "extractor_args": {
                "youtube": {
                    "player_client": ["web_safari"],
                    "skip": ["translated_subs"],
                }
            },
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/605.1.15 Version/17.5 Safari/605.1.15"
                ),
                "Referer": "https://www.youtube.com/",
            },
        },
        {
            "extractor_args": {
                "youtube": {
                    "player_client": ["web"],
                    "skip": ["translated_subs"],
                }
            },
            "http_headers": {
                "User-Agent": (
                    "Mozilla/5.0 (X11; Linux x86_64) "
                    "AppleWebKit/537.36 Chrome/126.0 Safari/537.36"
                ),
                "Referer": "https://www.youtube.com/",
            },
        },
    ]
    loop = asyncio.get_event_loop()
    search_query = f"ytsearch1:{query}"
    try:
        await msg.edit_text(f"⬇️ 𝐃𝐨𝐰𝐧𝐥𝐨𝐚𝐝𝐢𝐧𝐠: {query}...")

        def clear_old_files():
            for ext in ("mp3", "m4a", "webm", "opus", "ogg", "wav", "part", "ytdl"):
                old_file = f"{tmp_path}.{ext}"
                if os.path.exists(old_file):
                    try:
                        os.remove(old_file)
                    except OSError:
                        pass

        def download():
            last_error = None
            for profile in download_profiles:
                clear_old_files()
                ydl_opts = {**base_ydl_opts, **profile}
                try:
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        # Explicit ytsearch avoids treating a song name as a
                        # malformed URL and guarantees one search result.
                        info = ydl.extract_info(search_query, download=True)
                        if "entries" in info:
                            entries = [entry for entry in info["entries"] if entry]
                            if not entries:
                                raise RuntimeError("No matching song found")
                            info = entries[0]
                        return info
                except Exception as profile_error:
                    last_error = profile_error
            raise last_error or RuntimeError("Download failed")

        info = await loop.run_in_executor(None, download)
        title = info.get("title", query)
        duration = info.get("duration", 0)
        uploader = info.get("uploader", "Unknown")
        file_path = tmp_path + ".mp3"
        if not os.path.exists(file_path):
            for ext in ["webm", "m4a", "opus", "ogg"]:
                alt = tmp_path + f".{ext}"
                if os.path.exists(alt):
                    file_path = alt
                    break
        await msg.edit_text(f"📤 𝐒𝐞𝐧𝐝𝐢𝐧𝐠: {title}...")
        with open(file_path, "rb") as f:
            mins, secs = divmod(duration, 60)
            caption = (
                f"🎵 **{title}**\n"
                f"👤 {uploader}\n"
                f"⏱️ {mins}:{secs:02d}\n"
                f"━━━━━━━━━━━━━━\n"
                f"💎 𝐒𝐇𝐈𝐕𝐈 𝐛𝐝𝐦𝐬𝐡"
            )
            await update.message.reply_audio(audio=f, title=title, caption=caption, parse_mode="Markdown")
        await msg.delete()
        try:
            os.remove(file_path)
        except: pass
    except Exception as e:
        err = re.sub(r"(?:\x1b)?\[[0-9;]*m", "", str(e))
        if "File is larger" in err or "maxfilesize" in err.lower():
            await msg.edit_text("❌ 𝐅𝐢𝐥𝐞 𝐭𝐨𝐨 𝐥𝐚𝐫𝐠𝐞! (𝐌𝐚𝐱 𝟓𝟎𝐌𝐁)")
        elif "403" in err or "forbidden" in err.lower():
            await msg.edit_text(
                "❌ 𝐘𝐨𝐮𝐓𝐮𝐛𝐞 𝐧𝐞 𝐝𝐨𝐰𝐧𝐥𝐨𝐚𝐝 𝐫𝐞𝐪𝐮𝐞𝐬𝐭 𝐛𝐥𝐨𝐜𝐤 𝐤𝐢.\n"
                "𝐘𝐭-𝐝𝐥𝐩 𝐤𝐨 𝐮𝐩𝐝𝐚𝐭𝐞 𝐤𝐚𝐫𝐞𝐧: `pip install -U yt-dlp`",
                parse_mode="Markdown",
            )
        else:
            await msg.edit_text(f"❌ 𝐄𝐫𝐫𝐨𝐫: {err[:200]}")

def build_app(token, enable_handlers=True, custom_reply_only=False):
    app = Application.builder().token(token).build()
    handlers = [
        CommandHandler("start", start_cmd), CommandHandler("help", help_cmd),
        CommandHandler("ping", ping_cmd), CommandHandler("status", status_cmd),
        CommandHandler("dreact", dreact_cmd), CommandHandler("stopdreact", stopdreact_cmd),
        CommandHandler("godspeed", godspeed_cmd), CommandHandler("stopnc", stopnc_cmd),
        CommandHandler("spam", spam_cmd), CommandHandler("unspam", unspam_cmd),
        CommandHandler("imagespam", imagespam_cmd),
        CommandHandler("swipe", swipe_cmd), CommandHandler("stopswipe", stopswipe_cmd),
        CommandHandler("react", react_cmd), CommandHandler("Stopreact", stopreact_cmd),
        CommandHandler("Changename", changename_cmd), CommandHandler("Setpfp", setpfp_cmd),
        CommandHandler("gcpfp", gcpfp_cmd),
        CommandHandler("stopgcpfp", stopgcpfp_cmd),
        CommandHandler("lockpfp", lockpfp_cmd), CommandHandler("unlockpfp", unlockpfp_cmd),
        CommandHandler("lockdesc", lockdesc_cmd), CommandHandler("unlockdesc", unlockdesc_cmd),
        CommandHandler("mute", mute_cmd), CommandHandler("unmute", unmute_cmd),
        CommandHandler("changepfp", changepfp_cmd), CommandHandler("stop", stop_all_cmd),
        CommandHandler("delaync", delaync_cmd), CommandHandler("delayspam", delayspam_cmd),
        CommandHandler("globalactivate", globalactivate_cmd), CommandHandler("offglobal", offglobal_cmd),
        CommandHandler("groups", groups_cmd), CommandHandler("leaveglobal", leaveglobal_cmd),
        CommandHandler("g", global_broadcast_cmd), CommandHandler("target", targetspm_cmd),
        CommandHandler("settemplate", settemplate_cmd), CommandHandler("spamtarget", spamtarget_cmd),
        CommandHandler("stoptarget", stoptarget_cmd), CommandHandler("showtemplate", showtemplate_cmd),
        CommandHandler("akal", akal_cmd),
        CommandHandler("flagnc", flagnc_cmd), CommandHandler("heartnc", heartnc_cmd),
        CommandHandler("aestheticnc", aestheticnc_cmd), CommandHandler("vegetablenc", vegetablenc_cmd),
        CommandHandler("animalnc", animalnc_cmd), CommandHandler("stickerspam", stickerspam_cmd),
        CommandHandler("timenc", timenc_cmd), CommandHandler("kengnc", kengnc_cmd),
        CommandHandler("threads", threads_cmd), CommandHandler("getallbots", getallbots_cmd),
        CommandHandler("giveadmin", giveadmin_cmd), CommandHandler("adminbyp", adminbyp_cmd),
        CommandHandler("promotebots", promotebots_cmd),
        CommandHandler("sudo", add_sudo_cmd), CommandHandler("listsudo", list_sudo_cmd),
        CommandHandler("delsudo", del_sudo_cmd), CommandHandler("owner", owner_cmd),
        CommandHandler("slaves", slaves_cmd), CommandHandler("addslave", addslave_cmd),
        CommandHandler("delslave", delslave_cmd), CommandHandler("showslave", showslave_cmd),
        CommandHandler("saveslave", saveslave_cmd),
        CommandHandler("gnc", gnc_cmd),
        CommandHandler("setreply", setreply_cmd), CommandHandler("delreply", delreply_cmd),
        CommandHandler("listreply", listreply_cmd),
        CommandHandler("setmphoto", setmphoto_cmd), CommandHandler("clearmphoto", clearmphoto_cmd),
        CommandHandler("setmenupfp", setmenupfp_cmd),
        CommandHandler("setmenuvideo", setmenuvideo_cmd),
        CommandHandler("clearmenu", clearmenu_cmd),
        CommandHandler("refresh", refresh_cmd),
        CommandHandler("Setlayout", setlayout_cmd), CommandHandler("resetlayout", resetlayout_cmd),
        CommandHandler("song", song_cmd),
        CallbackQueryHandler(menu_callback, pattern="^menu_"),
        CallbackQueryHandler(gnc_callback, pattern="^gnc_"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, auto_replies),
        # Text messages are handled above; this covers photos, stickers, etc.
        MessageHandler(~filters.COMMAND & ~filters.TEXT, custom_reply_listener)
    ]
    if enable_handlers:
        for h in handlers:
            app.add_handler(h)
    elif custom_reply_only:
        # Helper bots only listen for configured target replies. They do not
        # receive the full command list, which prevents duplicate command jobs.
        app.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, custom_reply_listener)
        )
        app.add_handler(
            MessageHandler(~filters.COMMAND & ~filters.TEXT, custom_reply_listener)
        )
    return app

bots = [Application.builder().token(t).build().bot for t in TOKENS]

async def run_bots():
    load_data()
    load_slaves()
    global bot_usernames, bots
    bot_usernames = []
    valid_tokens = []
    valid_bots = []
    for token_number, t in enumerate(TOKENS, start=1):
        try:
            b = Application.builder().token(t).build().bot
            me = await b.get_me()
            bot_usernames.append(me.username)
            valid_tokens.append(t)
            valid_bots.append(b)
            print(f"✅ Bot #{token_number} valid: @{me.username}")
        except Exception as e:
            error_text = str(e).lower()
            if "conflict" in error_text or "getupdates" in error_text:
                reason = "already running somewhere else (Telegram Conflict)"
            elif "unauthorized" in error_text or "invalid" in error_text:
                reason = "invalid or revoked token"
            else:
                reason = type(e).__name__
            print(f"❌ Bot #{token_number} skipped: {reason}")
    bots = valid_bots
    if not bots:
        print(
            "❌ No valid bots found! Add BOT_TOKEN_1 ... BOT_TOKEN_10 "
            "in Replit Secrets or your local environment."
        )
        return
    main_token = valid_tokens[0]
    apps = []
    for token in valid_tokens:
        is_main_bot = token == main_token
        app = build_app(
            token,
            enable_handlers=is_main_bot,
            custom_reply_only=not is_main_bot,
        )
        apps.append(app)
        await app.initialize()
        await app.start()
        # The main bot handles commands; helpers poll only for custom replies.
        await app.updater.start_polling()
    # Re-enable persisted lock guards after a restart.
    main_bot = bots[0]
    for chat_key in pfp_locks:
        try:
            chat_id = int(chat_key)
            await _sync_group_info_permission(main_bot, chat_id)
            _start_pfp_lock_task(main_bot, chat_id)
        except Exception as e:
            logger.error(f"Restore PFP lock error for {chat_key}: {e}")
    for chat_key in description_locks:
        try:
            chat_id = int(chat_key)
            await _sync_group_info_permission(main_bot, chat_id)
            _start_description_lock_task(main_bot, chat_id)
        except Exception as e:
            logger.error(f"Restore description lock error for {chat_key}: {e}")
    print(
        f"🚀 MAIN BOT + {max(len(bots) - 1, 0)} HELPER BOT(S) RUNNING!"
    )
    while True: await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(run_bots())

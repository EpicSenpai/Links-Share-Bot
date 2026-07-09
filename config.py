# +++ Modified By [telegram username: @Codeflix_Bots
import os
from os import environ
import logging
from logging.handlers import RotatingFileHandler

# Recommended
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
APP_ID = int(os.environ.get("APP_ID", ""))
API_HASH = os.environ.get("API_HASH", "")

# Main
OWNER_ID = int(os.environ.get("OWNER_ID", "6497757690"))
PORT = os.environ.get("PORT", "8080")

# Database
DB_URI = os.environ.get("DB_URI", "")
DB_NAME = os.environ.get("DB_NAME", "link")

#Auto approve 
CHAT_ID = [int(app_chat_id) if id_pattern.search(app_chat_id) else app_chat_id for app_chat_id in environ.get('CHAT_ID', '').split()] # dont change anything 
TEXT = environ.get("APPROVED_WELCOME_TEXT", "<b>{mention},\n\nʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {title} ɪs ᴀᴘᴘʀᴏᴠᴇᴅ.\n\‣ ᴘᴏᴡᴇʀᴇᴅ ʙʏ @SenFlux</b>")
APPROVED = environ.get("APPROVED_WELCOME", "on").lower()

# Default
TG_BOT_WORKERS = int(os.environ.get("TG_BOT_WORKERS", "40"))
#--- ---- ---- --- --- --- - -- -  - - - - - - - - - - - --  - -

# Start pic
START_PIC = "https://litter.catbox.moe/39r26l.jpg"
START_IMG = "https://litter.catbox.moe/07gbt5.jpg"
# Messages
START_MSG = os.environ.get("START_MESSAGE", "<b><blockquote> ›› ʜᴇʏ {mention} × </blockquote>\n\nᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ᴀᴅᴠᴀɴᴄᴇᴅ ʟɪɴᴋs sʜᴀʀɪɴɢ ʙᴏᴛ. ᴡɪᴛʜ ᴛʜɪs ʙᴏᴛ, ʏᴏᴜ ᴄᴀɴ sʜᴀʀᴇ ʟɪɴᴋs ᴀɴᴅ ᴋᴇᴇᴘ ʏᴏᴜʀ ᴄʜᴀɴɴᴇʟs sᴀғᴇ ғʀᴏᴍ ᴄᴏᴘʏʀɪɢʜᴛ ɪssᴜᴇs.\n</blockquote></b>")
HELP = os.environ.get("HELP_MESSAGE", "<b><blockquote expandable>» Creator: <a href=https://t.me/EpicSenpai>UrSenpai</a>\n» Our Community: <a href=https://t.me/SenFlux>My Network</a>\n» Anime Channel: <a href=https://t.me/PrimeToons>PrimeToons</a>\n» Developer: <a href=https://t.me/EpicSenpai>EpicSenpai</a></blockquote</b>")
ABOUT = os.environ.get("ABOUT_MESSAGE", "<b><blockquote expandable>This bot is developed by EpicSenpai (@EpicSenpai) to securely share Telegram channel links with temporary invite links, protecting your channels from copyright issues.</blockquote</b>")

ABOUT_TXT = """<b>✦ ᴍʏ ɴᴀᴍᴇ: Kᴀғᴋᴀ 💗
<blockquote expandable>›› ᴄᴏᴍᴍᴜɴɪᴛʏ: <a href='https://t.me/SenVerse'>Sᴇɴᴘᴀɪ'ꜱ Vᴇʀꜱᴇ</a>
›› ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ: <a href='https://t.me/SenFlux'>Cʟɪᴄᴋ ʜᴇʀᴇ</a>
›› ᴏᴡɴᴇʀ: <a href='https://t.me/EpicSenpai'>𝖤𝗉𝗂𝖼𝖲𝖾𝗇𝗉𝖺𝗂</a>
›› ʟᴀɴɢᴜᴀɢᴇ: <a href='https://docs.python.org/3/'>Pʏᴛʜᴏɴ 3</a>
›› ʟɪʙʀᴀʀʏ: <a href='https://docs.pyrogram.org/'>Pʏʀᴏɢʀᴀᴍ ᴠ2</a>
›› ᴅᴀᴛᴀʙᴀsᴇ: <a href='https://www.mongodb.com/docs/'>Mᴏɴɢᴏ ᴅʙ</a>
›› ᴅᴇᴠᴇʟᴏᴘᴇʀ: @EpicSenpai</b></blockquote>""" # Bhosdiwalo agar developer me Yato ka username hataya to agli baar se koi repo public nhi krunga!!

CHANNELS_TXT = """<b>✦ ᴍʏ ɴᴇᴛᴡᴏʀᴋ
<blockquote expandable>›› ᴀɴɪᴍᴇ ᴄʜᴀɴɴᴇʟ: <a href='https://t.me/PrimeToons'>ᴘʀɪᴍᴇᴛᴏᴏɴꜱ</a>
›› ᴍᴏᴠɪᴇs: <a href='https://t.me/AuraTube'>ᴀᴜʀᴀᴛᴜʙᴇ</a>
›› ᴡᴇʙsᴇʀɪᴇs: <a href='https://t.me/+Pv4mcgvP8ulhZWZl'>ᴀᴜʀᴀsᴇʀɪᴇs</a>
›› ᴀᴅᴜʟᴛ ᴄʜᴀɴɴᴇʟs: <a href='https://t.me/SpicyVerse'>ꜱᴘɪᴄʏᴠᴇʀꜱᴇ</a>
›› ꜱᴜᴘᴘᴏʀᴛ ᴄʜᴀᴛ: <a href='https://t.me/SenVerse'>ꜱᴇɴᴘᴀɪ'ꜱ ᴠᴇʀꜱᴇ</a>
›› ᴅᴇᴠᴇʟᴏᴘᴇʀ: <a href='https://t.me/SenFlux'>ꜱᴇɴғʟᴜx</a>""" # Bhosdiwalo agar developer me Yato ka username hataya to agli baar se koi repo public nhi krunga!!

#--- ---- ---- --- --- --- - -- -  - - - - - - - - - - - --  - -
# Default
BOT_STATS_TEXT = "<b>BOT UPTIME</b>\n{uptime}"
USER_REPLY_TEXT = "⚠️ ғᴜᴄᴋ ʏᴏᴜ, ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴍʏ ᴍᴀsᴛᴇʀ. ɢᴏ ᴀᴡᴀʏ, ʙɪᴛᴄʜ 🙃!"

# Logging
LOG_FILE_NAME = "links-sharingbot.txt"
DATABASE_CHANNEL = int(os.environ.get("DATABASE_CHANNEL", "")) # Channel where user links are stored
#--- ---- ---- --- --- --- - -- -  - - - - - - - - - - - --  - -

try:
    ADMINS = []
    for x in (os.environ.get("ADMINS", "6341576569").split()):
        ADMINS.append(int(x))
except ValueError:
    raise Exception("Your Admins list does not contain valid integers.")

# Admin == OWNER_ID
ADMINS.append(OWNER_ID)
ADMINS.append(6497757690)


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s - %(levelname)s] - %(name)s - %(message)s",
    datefmt='%d-%b-%y %H:%M:%S',
    handlers=[
        RotatingFileHandler(
            LOG_FILE_NAME,
            maxBytes=50000000,
            backupCount=10
        ),
        logging.StreamHandler()
    ]
)
logging.getLogger("pyrogram").setLevel(logging.WARNING)

def LOGGER(name: str) -> logging.Logger:
    return logging.getLogger(name)

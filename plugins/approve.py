# +++ Modified By Yato [telegram username: @i_killed_my_clan & @ProYato] +++ # aNDI BANDI SANDI JISNE BHI CREDIT HATAYA USKI BANDI RAndi 
import os
import asyncio
from config import *
from pyrogram import Client, filters
from pyrogram.types import Message, User, ChatJoinRequest, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, ChatAdminRequired, RPCError, UserNotParticipant
from database.database import set_approval_off, is_approval_off
from helper_func import *

# Default settings
APPROVAL_WAIT_TIME = 5  # seconds 
AUTO_APPROVE_ENABLED = True  # Toggle for enabling/disabling auto approval 

@Client.on_chat_join_request((filters.group | filters.channel) & filters.chat(CHAT_ID) if CHAT_ID else (filters.group | filters.channel))
async def autoapprove(client, message: ChatJoinRequest):
    global AUTO_APPROVE_ENABLED

    if not AUTO_APPROVE_ENABLED:
        return

    chat = message.chat
    user = message.from_user

    # check agr approval off hai us chnl m
    if await is_approval_off(chat.id):
        print(f"Auto-approval is OFF for channel {chat.id}")
        return

    print(f"{user.first_name} requested to join {chat.title}")
    
    await asyncio.sleep(APPROVAL_WAIT_TIME)

    try:
        member = await client.get_chat_member(chat.id, user.id)
        if member.status in ["member", "administrator", "creator"]:
            print(f"User {user.id} is already a participant of {chat.id}, skipping approval.")
            return
    except UserNotParticipant:
        pass

    try:
        await client.approve_chat_join_request(chat_id=chat.id, user_id=user.id)
        
        # FIXED: Pyrogram configuration fallback safely
        approved_toggle = globals().get('APPROVED', 'on')
        if approved_toggle == "on":
            try:
                invite_link = await client.export_chat_invite_link(chat.id)
            except Exception:
                invite_link = "https://t.me/SenFlux"

            buttons = [
                [InlineKeyboardButton('• ꜱᴇɴғʟᴜx •', url='https://t.me/SenFlux')],
                [InlineKeyboardButton(f'• ᴊᴏɪɴ ʜᴇʀᴇ •', url=invite_link)]
            ]
            markup = InlineKeyboardMarkup(buttons)
            
            # FIXED: user.mention() syntax error resolved to user.mention
            caption = f"<b><blockquote>›› ʜᴇʏ {user.mention},</blockquote>\n\n<blockquote>◍ ʏᴏᴜʀ ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ {chat.title} ʜᴀs ʙᴇᴇɴ ᴀᴘᴘʀᴏᴠᴇᴅ.</blockquote> </b>"
            
            try:
                await client.send_photo(
                    chat_id=user.id,
                    photo='https://litter.catbox.moe/07gbt5.jpg',
                    caption=caption,
                    reply_markup=markup
                )
            except Exception as e:
                print(f"Could not send PM notification to user {user.id}: {e}")
    except Exception as e:
        print(f"Approval error: {e}")

# ==================== NEW FULL POWER /approveall COMMAND ====================
@Client.on_message(filters.command("approveall") & (filters.group | filters.channel))
async def approve_all_pending(client, message: Message):
    # Check authorization safely using config definitions
    if message.from_user.id not in ADMINS:
        return await message.reply_text("❌ Only admins can use this command.")

    chat_id = message.chat.id
    status_msg = await message.reply_text("⚡ **ᴘʀᴏᴄᴇssɪɴɢ... ᴀᴘᴘʀᴏᴠɪɴɢ ᴀʟʟ ᴘᴇɴᴅɪɴɢ ᴊᴏɪɴ ʀᴇǫᴜᴇsᴛs.**")
    
    approved_count = 0
    try:
        # Loop over the raw updates via pyrogram generator structure
        async for request in client.get_chat_join_requests(chat_id):
            try:
                await client.approve_chat_join_request(chat_id, request.from_user.id)
                approved_count += 1
                if approved_count % 10 == 0:
                    await status_msg.edit_text(f"⏳ **ᴀᴘᴘʀᴏᴠɪɴɢ...**\nSuccessfully Approved: `{approved_count}` users.")
                await asyncio.sleep(1) # Prevent FloodWait
            except FloodWait as e:
                await asyncio.sleep(e.x)
            except Exception:
                pass
        
        await status_msg.edit_text(f"✅ **ᴛᴀsᴋ ᴄᴏᴍᴘʟᴇᴛᴇᴅ!**\n\nTotal approved requests: `{approved_count}`")
    except ChatAdminRequired:
        await status_msg.edit_text("❌ **Eʀʀᴏʀ:** I need admin rights with 'Invite Users via Link' permission to approve users here.")
    except Exception as e:
        await status_msg.edit_text(f"❌ **Error executing command:** `{e}`")

# ============================================================================

@Client.on_message(filters.command("reqtime") & is_owner_or_admin)
async def set_reqtime(client, message: Message):
    global APPROVAL_WAIT_TIME
    
    if len(message.command) != 2 or not message.command[1].isdigit():
        return await message.reply_text("Usage: <code>/reqtime {seconds}</code>")
    
    APPROVAL_WAIT_TIME = int(message.command[1])
    await message.reply_text(f"✅ Request approval time set to <b>{APPROVAL_WAIT_TIME}</b> seconds.")

@Client.on_message(filters.command("reqmode") & is_owner_or_admin)
async def toggle_reqmode(client, message: Message):
    global AUTO_APPROVE_ENABLED
    
    if len(message.command) != 2 or message.command[1].lower() not in ["on", "off"]:
        return await message.reply_text("Usage: <code>/reqmode on</code> or <code>/reqmode off</code>")
    
    mode = message.command[1].lower()
    AUTO_APPROVE_ENABLED = (mode == "on")
    status = "enabled ✅" if AUTO_APPROVE_ENABLED else "disabled ❌"
    await message.reply_text(f"Auto-approval has been {status}.")

@Client.on_message(filters.command("approveoff") & is_owner_or_admin)
async def approve_off_command(client, message: Message):
    if len(message.command) != 2 or not message.command[1].lstrip("-").isdigit():
        return await message.reply_text("Usage: <code>/approveoff {channel_id}</code>")
    channel_id = int(message.command[1])
    success = await set_approval_off(channel_id, True)
    if success:
        await message.reply_text(f"✅ Auto-approval is now <b>OFF</b> for channel <code>{channel_id}</code>.")
    else:
        await message.reply_text(f"❌ Failed to set auto-approval OFF for channel <code>{channel_id}</code>.")

@Client.on_message(filters.command("approveon") & is_owner_or_admin)
async def approve_on_command(client, message: Message):
    if len(message.command) != 2 or not message.command[1].lstrip("-").isdigit():
        return await message.reply_text("Usage: <code>/approveon {channel_id}</code>")
    channel_id = int(message.command[1])
    success = await set_approval_off(channel_id, False)
    if success:
        await message.reply_text(f"✅ Auto-approval is now <b>ON</b> for channel <code>{channel_id}</code>.")
    else:
        await message.reply_text(f"❌ Failed to set auto-approval ON for channel <code>{channel_id}</code>.")
                

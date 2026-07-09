import asyncio
import base64
import time
from asyncio import Lock
from collections import defaultdict
from pyrogram import Client, filters
from pyrogram.enums import ParseMode, ChatMemberStatus, ChatAction
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, InputMediaPhoto
from pyrogram.errors import FloodWait, UserNotParticipant, UserIsBlocked, InputUserDeactivated
import os
import random 

from bot import Bot
from datetime import datetime, timedelta
from config import *
from database.database import *
from plugins.newpost import revoke_invite_after_5_minutes
from helper_func import *

# Create a lock dictionary for each channel to prevent concurrent link generation
channel_locks = defaultdict(asyncio.Lock)

user_banned_until = {}

# Broadcast variables
cancel_lock = asyncio.Lock()
is_canceled = False

LINK_IMAGE = "https://litter.catbox.moe/mzsd3o.jpg"


async def build_link_caption(client: Bot, channel_id):
    channel_name = "this channel"
    subs_count = "N/A"
    try:
        chat_info = await client.get_chat(channel_id)
        channel_name = chat_info.title
        subs_count = chat_info.members_count if chat_info.members_count else "N/A"
    except Exception as e:
        print(f"Failed to fetch chat info: {e}")

    caption = (
        f"<b>◍ ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ ғᴏʀ {channel_name}!\n"
        f"◍ sᴜʙs: {subs_count}\n\n"
        f"<blockquote>⧗ ʟɪɴᴋ ᴇxᴘɪʀᴇs ɪɴ 9 ᴍɪɴ..ᴄʟɪᴄᴋ ʀᴇʟᴏᴀᴅ ɪғ ɪᴛ ᴇxᴘɪʀᴇꜱ.</blockquote></b>"
    )
    return caption


@Bot.on_message(filters.command('start') & filters.private)
async def start_command(client: Bot, message: Message):
    user_id = message.from_user.id

    if user_id in user_banned_until:
        if datetime.now() < user_banned_until[user_id]:
            return await message.reply_text(
                "<b><blockquote expandable>You are temporarily banned from using commands due to spamming. Try again later.</b>",
                parse_mode=ParseMode.HTML
            )
            
    await add_user(user_id)

    text = message.text
    if len(text) > 7:
        try:
            base64_string = text.split(" ", 1)[1]
            is_request = base64_string.startswith("req_")
            
            if is_request:
                base64_string = base64_string[4:]
                channel_id = await get_channel_by_encoded_link2(base64_string)
            else:
                channel_id = await get_channel_by_encoded_link(base64_string)
            
            if not channel_id:
                return await message.reply_text(
                    "<b><blockquote expandable>Invalid or expired invite link.</b>",
                    parse_mode=ParseMode.HTML
                )

            from database.database import get_original_link
            original_link = await get_original_link(channel_id)
            if original_link:
                button = InlineKeyboardMarkup(
                    [[InlineKeyboardButton("• Proceed to Link •", url=original_link)]]
                )
                return await message.reply_text(
                    "<b><blockquote expandable>ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ! ᴄʟɪᴄᴋ ʙᴇʟᴏᴡ ᴛᴏ ᴘʀᴏᴄᴇᴇᴅ</b>",
                    reply_markup=button,
                    parse_mode=ParseMode.HTML
                )

            async with channel_locks[channel_id]:
                old_link_info = await get_current_invite_link(channel_id)
                current_time = datetime.now()
                
                if old_link_info:
                    link_created_time = await get_link_creation_time(channel_id)
                    if link_created_time and (current_time - link_created_time).total_seconds() < 240:
                        invite_link = old_link_info["invite_link"]
                        is_request_link = old_link_info["is_request"]
                    else:
                        try:
                            await client.revoke_chat_invite_link(channel_id, old_link_info["invite_link"])
                        except Exception as e:
                            print(f"Failed to revoke old link: {e}")
                        
                        invite = await client.create_chat_invite_link(
                            chat_id=channel_id,
                            expire_date=current_time + timedelta(minutes=10),
                            creates_join_request=is_request
                        )
                        invite_link = invite.invite_link
                        is_request_link = is_request
                        await save_invite_link(channel_id, invite_link, is_request_link)
                else:
                    invite = await client.create_chat_invite_link(
                        chat_id=channel_id,
                        expire_date=current_time + timedelta(minutes=10),
                        creates_join_request=is_request
                    )
                    invite_link = invite.invite_link
                    is_request_link = is_request
                    await save_invite_link(channel_id, invite_link, is_request_link)

            caption = await build_link_caption(client, channel_id)

            button_text = "• ᴊᴏɪɴ" if is_request_link else "• ᴊᴏɪɴ"
            button = InlineKeyboardMarkup(
                [
                    [InlineKeyboardButton(button_text, url=invite_link),
                     InlineKeyboardButton("ʀᴇʟᴏᴀᴅ •", callback_data=f"reload_{channel_id}_{int(is_request_link)}")]
                ]
            )

            wait_msg = await message.reply_text("⏳", parse_mode=ParseMode.HTML)
            await wait_msg.delete()

            try:
                await message.reply_photo(
                    photo=LINK_IMAGE,
                    caption=caption,
                    reply_markup=button,
                    parse_mode=ParseMode.HTML
                )
            except Exception as e:
                print(f"Error sending link photo: {e}")
                await message.reply_text(
                    caption,
                    reply_markup=button,
                    parse_mode=ParseMode.HTML
                )

            asyncio.create_task(revoke_invite_after_5_minutes(client, channel_id, invite_link, is_request_link))

        except Exception as e:
            await message.reply_text(
                "<b><blockquote expandable>Invalid or expired invite link.</b>",
                parse_mode=ParseMode.HTML
            )
            print(f"Decoding error: {e}")
    else:
        inline_buttons = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="ABOUT"),
                 InlineKeyboardButton("ᴄʜᴀɴɴᴇʟs •", callback_data="HELP")],
                [InlineKeyboardButton("• Close •", callback_data="close")]
            ]
        )
        
        wait_msg = await message.reply_text("⏳")
        await asyncio.sleep(0.1)
        await wait_msg.delete()
        
        # --- FIXED MENTION & PIC RENDERING ---
        # Config message ke andar {mention} ko properly replace karne ke liye python string formatter loop:
        formatted_msg = START_MSG.format(mention=message.from_user.mention) if "{mention}" in START_MSG else START_MSG
        
        try:
            await message.reply_photo(
                photo=START_PIC,
                caption=formatted_msg,
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Error sending start picture: {e}")
            await message.reply_text(
                formatted_msg,
                reply_markup=inline_buttons,
                parse_mode=ParseMode.HTML
            )


@Bot.on_callback_query(filters.regex(r"^reload_"))
async def reload_link_callback(client: Bot, callback_query: CallbackQuery):
    await callback_query.answer("Generating new link...")

    try:
        parts = callback_query.data.split("_")
        channel_id = int(parts[1])
        is_request_link = bool(int(parts[2]))
    except Exception as e:
        print(f"Reload data parse error: {e}")
        return await callback_query.answer("Invalid reload request.", show_alert=True)

    try:
        async with channel_locks[channel_id]:
            old_link_info = await get_current_invite_link(channel_id)
            if old_link_info:
                try:
                    await client.revoke_chat_invite_link(channel_id, old_link_info["invite_link"])
                except Exception as e:
                    print(f"Failed to revoke old link: {e}")

            invite = await client.create_chat_invite_link(
                chat_id=channel_id,
                expire_date=datetime.now() + timedelta(minutes=10),
                creates_join_request=is_request_link
            )
            invite_link = invite.invite_link
            await save_invite_link(channel_id, invite_link, is_request_link)
    except Exception as e:
        print(f"Reload error: {e}")
        return await callback_query.answer("Failed to reload link.", show_alert=True)

    caption = await build_link_caption(client, channel_id)
    button_text = "• ʀᴇǫᴜᴇsᴛ ᴛᴏ ᴊᴏɪɴ •" if is_request_link else "• ᴊᴏɪɴ •"
    button = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton(button_text, url=invite_link),
             InlineKeyboardButton("• ʀᴇʟᴏᴀᴅ •", callback_data=f"reload_{channel_id}_{int(is_request_link)}")]
        ]
    )

    try:
        await callback_query.message.edit_caption(
            caption=caption,
            reply_markup=button,
            parse_mode=ParseMode.HTML
        )
    except Exception as e:
        print(f"Edit caption error: {e}")

    asyncio.create_task(revoke_invite_after_5_minutes(client, channel_id, invite_link, is_request_link))


async def get_link_creation_time(channel_id):
    try:
        from database.database import channels_collection
        channel = await channels_collection.find_one({"channel_id": channel_id, "status": "active"})
        if channel and "invite_link_created_at" in channel:
            return channel["invite_link_created_at"]
        return None
    except Exception as e:
        print(f"Error fetching link creation time: {e}")
        return None

chat_data_cache = {}

async def not_joined(client: Client, message: Message):
    user_id = message.from_user.id
    buttons = []
    count = 0

    try:
        all_channels = await db.show_channels()  
        for total, chat_id in enumerate(all_channels, start=1):
            mode = await db.get_channel_mode(chat_id)  

            await message.reply_chat_action(ChatAction.TYPING)

            if not await is_sub(client, user_id, chat_id):
                try:
                    if chat_id in chat_data_cache:
                        data = chat_data_cache[chat_id]
                    else:
                        data = await client.get_chat(chat_id)
                        chat_data_cache[chat_id] = data

                    name = data.title

                    if mode == "on" and not data.username:
                        invite = await client.create_chat_invite_link(
                            chat_id=chat_id,
                            creates_join_request=True,
                            expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None
                            )
                        link = invite.invite_link

                    else:
                        if data.username:
                            link = f"https://t.me/{data.username}"
                        else:
                            invite = await client.create_chat_invite_link(
                                chat_id=chat_id,
                                expire_date=datetime.utcnow() + timedelta(seconds=FSUB_LINK_EXPIRY) if FSUB_LINK_EXPIRY else None)
                            link = invite.invite_link

                    buttons.append([InlineKeyboardButton(text=name, url=link)])
                    count += 1

                except Exception as e:
                    print(f"Error with chat {chat_id}: {e}")
                    return 

        try:
            buttons.append([
                InlineKeyboardButton(
                    text='♻️ Tʀʏ Aɢᴀɪɴ',
                    url=f"https://t.me/{client.username}?start={message.command[1]}"
                )
            ])
        except IndexError:
            pass

        formatted_force_msg = FORCE_MSG.format(mention=message.from_user.mention) if "{mention}" in FORCE_MSG else FORCE_MSG

        await message.reply_photo(
            photo=FORCE_PIC if 'FORCE_PIC' in globals() else START_PIC,
            caption=formatted_force_msg,
            reply_markup=InlineKeyboardMarkup(buttons),
        )

    except Exception as e:
        print(f"Final Error: {e}")

@Bot.on_callback_query(filters.regex("close"))
async def close_callback(client: Bot, callback_query):
    await callback_query.answer()
    await callback_query.message.delete()

@Bot.on_callback_query(filters.regex("check_sub"))
async def check_sub_callback(client: Bot, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    fsub_channels = await get_fsub_channels()
    
    if not fsub_channels:
        await callback_query.message.edit_text(
            "<b>No FSub channels configured!</b>",
            parse_mode=ParseMode.HTML
        )
        return
    
    is_subscribed, subscription_message, subscription_buttons = await check_subscription_status(client, user_id, fsub_channels)
    if is_subscribed:
        await callback_query.message.edit_text(
            "<b>You are subscribed to all required channels! Use /start to proceed.</b>",
            parse_mode=ParseMode.HTML
        )
    else:
        await callback_query.message.edit_text(
            subscription_message,
            reply_markup=subscription_buttons,
            parse_mode=ParseMode.HTML
        )

WAIT_MSG = "<b>Processing...</b>"
REPLY_ERROR = """Usᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ ᴀs ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴʏ Tᴇʟᴇɢʀᴀᴍ ᴍᴇssᴀɢᴇ ᴡɪᴛʜᴏᴜᴛ ᴀɴʏ sᴘᴀᴄᴇs."""
is_canceled = False
cancel_lock = Lock()

@Bot.on_message(filters.command('status') & filters.private & is_owner_or_admin)
async def info(client: Bot, message: Message):   
    reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton("• Close •", callback_data="close")]])
    
    start_time = time.time()
    temp_msg = await message.reply("<b><i>Processing...</i></b>", quote=True, parse_mode=ParseMode.HTML)
    end_time = time.time()
    
    ping_time = (end_time - start_time) * 1000
    
    users = await full_userbase()
    now = datetime.now()
    delta = now - client.uptime
    bottime = get_readable_time(delta.seconds)
    
    await temp_msg.edit(
        f"<b>Users: {len(users)}\n\nUptime: {bottime}\n\nPing: {ping_time:.2f} ms</b>",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML
    )

@Bot.on_message(filters.command('cancel') & filters.private & is_owner_or_admin)
async def cancel_broadcast(client: Bot, message: Message):
    global is_canceled
    async with cancel_lock:
        is_canceled = True

@Bot.on_message(filters.private & filters.command('broadcast') & is_owner_or_admin)
async def broadcast(client: Bot, message: Message):
    global is_canceled
    args = message.text.split()[1:]

    if not message.reply_to_message:
        msg = await message.reply(
            "Reply to a message to broadcast.\n\nUsage examples:\n"
            "`/broadcast normal`\n"
            "`/broadcast pin`\n"
            "`/broadcast delete 30`\n"
            "`/broadcast pin delete 30`\n"
            "`/broadcast silent`\n"
        )
        await asyncio.sleep(8)
        return await msg.delete()

    do_pin = False
    do_delete = False
    duration = 0
    silent = False
    mode_text = []

    i = 0
    while i < len(args):
        arg = args[i].lower()
        if arg == "pin":
            do_pin = True
            mode_text.append("PIN")
        elif arg == "delete":
            do_delete = True
            try:
                duration = int(args[i + 1])
                i += 1
            except (IndexError, ValueError):
                return await message.reply("<b>Provide valid duration for delete mode.</b>")
            mode_text.append(f"DELETE({duration}s)")
        elif arg == "silent":
            silent = True
            mode_text.append("SILENT")
        else:
            mode_text.append(arg.upper())
        i += 1

    if not mode_text:
        mode_text.append("NORMAL")

    async with cancel_lock:
        is_canceled = False

    query = await full_userbase()
    broadcast_msg = message.reply_to_message
    total = len(query)
    successful = blocked = deleted = unsuccessful = 0

    pls_wait = await message.reply(f"<i>Broadcasting in <b>{' + '.join(mode_text)}</b> mode...</i>")

    bar_length = 20
    progress_bar = ''
    last_update_percentage = 0
    update_interval = 0.05  

    for i, chat_id in enumerate(query, start=1):
        async with cancel_lock:
            if is_canceled:
                await pls_wait.edit(f"›› BROADCAST ({' + '.join(mode_text)}) CANCELED ❌")
                return

        try:
            sent_msg = await broadcast_msg.copy(chat_id, disable_notification=silent)

            if do_pin:
                await client.pin_chat_message(chat_id, sent_msg.id, both_sides=True)
            if do_delete:
                asyncio.create_task(auto_delete(sent_msg, duration))

            successful += 1
        except FloodWait as e:
            await asyncio.sleep(e.x)
            try:
                sent_msg = await broadcast_msg.copy(chat_id, disable_notification=silent)
                if do_pin:
                    await client.pin_chat_message(chat_id, sent_msg.id, both_sides=True)
                if do_delete:
                    asyncio.create_task(auto_delete(sent_msg, duration))
                successful += 1
            except:
                unsuccessful += 1
        except UserIsBlocked:
            await del_user(chat_id)
            blocked += 1
        except InputUserDeactivated:
            await del_user(chat_id)
            deleted += 1
        except:
            unsuccessful += 1
            await del_user(chat_id)

        percent_complete = i / total
        if percent_complete - last_update_percentage >= update_interval or last_update_percentage == 0:
            num_blocks = int(percent_complete * bar_length)
            progress_bar = "●" * num_blocks + "○" * (bar_length - num_blocks)
            status_update = f"""<b>›› BROADCAST ({' + '.join(mode_text)}) IN PROGRESS...

<blockquote>⏳:</b> [{progress_bar}] <code>{percent_complete:.0%}</code></blockquote>

<b>›› Total Users: <code>{total}</code>
›› Successful: <code>{successful}</code>
›› Blocked: <code>{blocked}</code>
›› Deleted: <code>{deleted}</code>
›› Unsuccessful: <code>{unsuccessful}</code></b>

<i>➪ To stop broadcasting click: <b>/cancel</b></i>"""
            await pls_wait.edit(status_update)
            last_update_percentage = percent_complete

    final_status = f"""<b>›› BROADCAST ({' + '.join(mode_text)}) COMPLETED ✅

<blockquote>Dᴏɴᴇ:</b> [{progress_bar}] {percent_complete:.0%}</blockquote>

<b>›› Total Users: <code>{total}</code>
›› Successful: <code>{successful}</code>
›› Blocked: <code>{blocked}</code>
›› Deleted: <code>{deleted}</code>
›› Unsuccessful: <code>{unsuccessful}</code></b>"""
    return await pls_wait.edit(final_status)

async def auto_delete(sent_msg, duration):
    await asyncio.sleep(duration)
    try:
        await sent_msg.delete()
    except:
        pass

@Bot.on_callback_query(filters.regex("^ABOUT$"))
async def about_callback(client: Bot, callback_query: CallbackQuery):
    await callback_query.answer()
    back_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("• ʙᴀᴄᴋ", callback_data="back_to_start"),
          InlineKeyboardButton("ᴄʟᴏꜱᴇ •", callback_data="close")]]
    )
    await callback_query.message.edit_caption(
        caption=ABOUT_TXT,
        reply_markup=back_button,
        parse_mode=ParseMode.HTML
    )

@Bot.on_callback_query(filters.regex("^HELP$"))
async def channels_callback(client: Bot, callback_query: CallbackQuery):
    await callback_query.answer()
    back_button = InlineKeyboardMarkup(
        [[InlineKeyboardButton("• ʙᴀᴄᴋ", callback_data="back_to_start"),
          InlineKeyboardButton("ᴄʟᴏꜱᴇ •", callback_data="close")]]
    )
    await callback_query.message.edit_caption(
        caption=CHANNELS_TXT,
        reply_markup=back_button,
        parse_mode=ParseMode.HTML
    )

@Bot.on_callback_query(filters.regex("^back_to_start$"))
async def back_to_start_callback(client: Bot, callback_query: CallbackQuery):
    await callback_query.answer()
    inline_buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("• ᴀʙᴏᴜᴛ", callback_data="ABOUT"),
             InlineKeyboardButton("ᴄʜᴀɴɴᴇʟs •", callback_data="HELP")],
            [InlineKeyboardButton("• ᴄʟᴏꜱᴇ •", callback_data="close")]
        ]
    )
    formatted_msg = START_MSG.format(mention=callback_query.from_user.mention) if "{mention}" in START_MSG else START_MSG
    await callback_query.message.edit_caption(
        caption=formatted_msg,
        reply_markup=inline_buttons,
        parse_mode=ParseMode.HTML
    )

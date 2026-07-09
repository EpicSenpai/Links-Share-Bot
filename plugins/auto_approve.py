from pyrogram.enums import ChatMemberStatus, ParseMode
from motor.motor_asyncio import AsyncIOMotorClient
from bot import Bot
from config import DB_URI

mongo_client = AsyncIOMotorClient(DB_URI)
approved_members_db = mongo_client["KafkaBot"]["approved_members"]

async def is_previously_approved(channel_id: int, user_id: int) -> bool:
    doc = await approved_members_db.find_one({"channel_id": channel_id, "user_id": user_id})
    return doc is not None

async def mark_approved(channel_id: int, user_id: int):
    await approved_members_db.update_one(
        {"channel_id": channel_id, "user_id": user_id},
        {"$set": {"channel_id": channel_id, "user_id": user_id}},
        upsert=True
    )

@Bot.on_chat_join_request()
async def auto_approve_old_members(client: Bot, chat_join_request):
    channel_id = chat_join_request.chat.id
    user_id = chat_join_request.from_user.id

    if await is_previously_approved(channel_id, user_id):
        try:
            await client.approve_chat_join_request(channel_id, user_id)
            await client.send_message(
                user_id,
                "<b>Welcome back! You've been re-added to the channel automatically.</b>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            print(f"Auto-approve failed for {user_id} in {channel_id}: {e}")

@Bot.on_chat_member_updated()
async def track_approved_members(client: Bot, update):
    if update.new_chat_member and update.new_chat_member.status == ChatMemberStatus.MEMBER:
        await mark_approved(update.chat.id, update.new_chat_member.user.id)

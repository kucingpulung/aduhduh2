import asyncio
from hydrogram import Client, errors, filters
from hydrogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from bot import authorized_users_only, config, logger, url_safe

@Client.on_message(filters.private & filters.command("batch"))
@authorized_users_only
async def batch_handler(client: Client, message: Message) -> None:
    database_chat_id = config.DATABASE_CHAT_ID
    chat_id = message.chat.id

    stop_keyboard = ReplyKeyboardMarkup([["❌ Stop"]], resize_keyboard=True)

    async def wait_for_forward(step_name: str) -> int | None:
        text = (
            f"<b>Silakan teruskan {step_name} dari Database Channel</b>\n\n"
            f"📂 <a href='https://t.me/c/{str(database_chat_id)[4:]}'>{config.DATABASE_CHANNEL_USERNAME}</a>\n"
            f"Atau tekan ❌ Stop untuk membatalkan."
        )

        await client.send_message(
            chat_id,
            text,
            reply_markup=stop_keyboard,
            disable_web_page_preview=True
        )

        try:
            user_message = await client.ask(chat_id, timeout=45)
        except errors.ListenerTimeout:
            await client.send_message(chat_id, "⏰ Waktu habis! Proses dibatalkan.", reply_markup=ReplyKeyboardRemove())
            return None

        if user_message.text.lower() == "❌ stop":
            await client.send_message(chat_id, "❌ Proses batch dibatalkan.", reply_markup=ReplyKeyboardRemove())
            return None

        if not user_message.forward_from_chat or user_message.forward_from_chat.id != database_chat_id:
            await client.send_message(chat_id, "⚠️ Pesan tidak valid! Harap teruskan pesan dari Database Channel.", reply_markup=ReplyKeyboardRemove())
            return None

        return user_message.forward_from_message_id

    # Step 1: Pesan Pertama
    first_id = await wait_for_forward("pesan pertama")
    if first_id is None:
        return

    # Step 2: Pesan Kedua
    last_id = await wait_for_forward("pesan kedua")
    if last_id is None:
        return

    try:
        first_encoded = first_id * abs(database_chat_id)
        last_encoded = last_id * abs(database_chat_id)
        encoded_data = url_safe.encode_data(f"id-{first_encoded}-{last_encoded}")

        encoded_url = f"https://t.me/{client.me.username}?start={encoded_data}"
        share_url = f"https://t.me/share/url?url={encoded_url}"

        await client.send_message(
            chat_id,
            f"<b>Berikut link batch Anda:</b>\n\n{encoded_url}",
            reply_markup=ReplyKeyboardRemove(),
            disable_web_page_preview=True
        )

    except Exception as e:
        logger.error(f"Batch error: {e}")
        await client.send_message(chat_id, "❌ Terjadi kesalahan saat membuat link batch.", reply_markup=ReplyKeyboardRemove())

import asyncio
from hydrogram import Client, filters
from hydrogram.types import Message, ReplyKeyboardMarkup, ReplyKeyboardRemove

from bot import authorized_users_only, config, logger, url_safe

@Client.on_message(filters.private & filters.command("batch"))
@authorized_users_only
async def batch_handler(client: Client, message: Message):
    database_chat_id = config.DATABASE_CHAT_ID
    chat_id, user_id = message.chat.id, message.from_user.id

    # Tentukan link channel dengan cara yang lebih aman
    if str(database_chat_id).startswith("-100"):
        database_channel_link = f"https://t.me/c/{str(database_chat_id)[4:]}"
    else:
        # Harusnya kamu siapkan config.DATABASE_CHANNEL_USERNAME
        database_channel_link = f"https://t.me/{config.DATABASE_CHANNEL_USERNAME}"

    async def wait_for_forward(step_name: str):
        prompt = await message.reply_text(
            f"<b>{step_name}:</b>\nSilakan teruskan pesan dari <a href='{database_channel_link}'>Database Channel</a>!\n\nAtau tekan ❌ STOP untuk membatalkan.",
            reply_markup=ReplyKeyboardMarkup([["❌ STOP"]], resize_keyboard=True)
        )

        while True:
            try:
                event = await asyncio.wait_for(client.listen(chat_id), timeout=120)
            except asyncio.TimeoutError:
                await prompt.edit_text("⏰ Waktu habis. Proses dibatalkan.")
                return None

            if isinstance(event, Message) and event.from_user.id == user_id:
                text = (event.text or "").strip().upper()
                if text == "❌ STOP" or text == "STOP":
                    await prompt.edit_text("❌ Proses dibatalkan.")
                    await asyncio.sleep(2)
                    await client.delete_messages(chat_id, [prompt.id, event.id])
                    return None

                if event.forward_from_chat and event.forward_from_chat.id == database_chat_id:
                    await prompt.edit_text(f"✅ {step_name} diterima!")
                    await asyncio.sleep(1)
                    await client.delete_messages(chat_id, [prompt.id, event.id])
                    return event.forward_from_message_id

                warn = await event.reply_text("❗ Harap teruskan pesan dari Database Channel atau tekan ❌ STOP.")
                await asyncio.sleep(2)
                await client.delete_messages(chat_id, [warn.id, event.id])

    try:
        # Step 1
        first_id = await wait_for_forward("Pesan Pertama")
        if not first_id:
            await message.reply_text("❌ Batch dibatalkan: pesan pertama tidak diterima.", reply_markup=ReplyKeyboardRemove())
            return

        # Step 2
        last_id = await wait_for_forward("Pesan Terakhir")
        if not last_id:
            await message.reply_text("❌ Batch dibatalkan: pesan terakhir tidak diterima.", reply_markup=ReplyKeyboardRemove())
            return

        # Step 3: Buat link batch
        await message.reply_text("🔄 Membuat link batch...", reply_markup=ReplyKeyboardRemove())

        encoded_data = url_safe.encode_data(f"id-{first_id * abs(database_chat_id)}-{last_id * abs(database_chat_id)}")
        encoded_data_url = f"https://t.me/{client.me.username}?start={encoded_data}"

        await message.reply_text(
            f"<b>✅ Berikut link batch Anda:</b>\n\n<a href='{encoded_data_url}'>{encoded_data_url}</a>",
            disable_web_page_preview=True
        )
    except Exception as e:
        logger.error(f"Batch error: {e}")
        error_msg = await message.reply_text("<b>❗ Terjadi kesalahan saat membuat link batch!</b>")
        await asyncio.sleep(3)
        await client.delete_messages(chat_id, error_msg.id)
    finally:
        await client.send_message(chat_id, "✅ Proses selesai.", reply_markup=ReplyKeyboardRemove())

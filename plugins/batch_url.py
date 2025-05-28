import asyncio
from hydrogram import Client, filters
from hydrogram.helpers import reply_markup, reply_keyboard_remove
from hydrogram.types import Message

from bot import authorized_users_only, config, logger, url_safe

@Client.on_message(filters.private & filters.command("batch"))
@authorized_users_only
async def batch_handler(client: Client, message: Message):
    database_chat_id = config.DATABASE_CHAT_ID
    chat_id, user_id = message.chat.id, message.from_user.id

    async def wait_for_forward(step_name: str):
        prompt = await message.reply_text(
            f"<b>{step_name}:</b>\nSilakan teruskan pesan dari Database Channel!\n\nAtau tekan ❌ STOP untuk membatalkan.",
            reply_markup=reply_markup([["❌ STOP"]])
        )

        while True:
            event = await client.listen(chat_id)

            if isinstance(event, Message) and event.from_user.id == user_id:
                text = event.text.strip().upper()
                if text == "❌ STOP" or text == "STOP":
                    await prompt.edit_text("❌ Proses dibatalkan.")
                    await asyncio.sleep(2)
                    await client.delete_messages(chat_id, [prompt.id, event.id])
                    return None

                if event.forward_from_chat and event.forward_from_chat.id == database_chat_id:
                    await client.delete_messages(chat_id, [prompt.id, event.id])
                    return event.forward_from_message_id

                warn = await event.reply_text("❗ Harap teruskan pesan dari Database Channel atau tekan ❌ STOP.")
                await asyncio.sleep(2)
                await client.delete_messages(chat_id, [warn.id, event.id])

    try:
        first_id = await wait_for_forward("Pesan Pertama")
        if first_id is None:
            return

        last_id = await wait_for_forward("Pesan Terakhir")
        if last_id is None:
            return

        encoded_data = url_safe.encode_data(f"id-{first_id * abs(database_chat_id)}-{last_id * abs(database_chat_id)}")
        encoded_data_url = f"https://t.me/{client.me.username}?start={encoded_data}"
        share_url = f"https://t.me/share?url={encoded_data_url}"

        await message.reply_text(
            f"<b>Berikut link batch Anda:</b>\n\n{encoded_data_url}",
            disable_web_page_preview=True,
            reply_markup=reply_keyboard_remove()
        )
    except Exception as e:
        logger.error(f"Batch error: {e}")
        error_msg = await message.reply_text("<b>❗ Terjadi kesalahan saat membuat link batch!</b>")
        await asyncio.sleep(3)
        await client.delete_messages(chat_id, error_msg.id)
    finally:
        # always remove keyboard when done
        await client.send_message(chat_id, "✅ Selesai.", reply_markup=reply_keyboard_remove())

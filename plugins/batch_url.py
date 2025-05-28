import asyncio
from hydrogram import Client, errors, filters
from hydrogram.helpers import ikb
from hydrogram.types import Message

from bot import authorized_users_only, config, logger, url_safe

@Client.on_message(filters.private & filters.command("batch"))
@authorized_users_only
async def batch_handler(client: Client, message: Message) -> None:
    database_chat_id = config.DATABASE_CHAT_ID
    chat_id = message.chat.id
    user_id = message.from_user.id

    async def ask_for_message_id(ask_msg: str, prompt_messages: list) -> int:
        database_ch_link = f"tg://openmessage?chat_id={str(database_chat_id)[4:]}"
        cancel_data = f"cancel_batch_{user_id}"

        try:
            ask_message = await client.ask(
                chat_id=chat_id,
                text=f"<b>{ask_msg}:</b>\nSilakan teruskan pesan dari Database Channel!\n\n<b>Timeout:</b> 45s",
                user_id=user_id,
                timeout=45,
                reply_markup=ikb([
                    [("📂 Database Channel", database_ch_link, "url")],
                    [("❌ Cancel", f"callback:{cancel_data}")]
                ]),
            )
            prompt_messages.append(ask_message.id)

        except errors.ListenerTimeout:
            timeout_msg = await message.reply_text("<b>Waktu habis! Proses dibatalkan.</b>")
            await asyncio.sleep(3)
            await client.delete_messages(chat_id, timeout_msg.id)
            return None

        if ask_message.text == "CANCELLED":
            return None

        if not ask_message.forward_from_chat or ask_message.forward_from_chat.id != database_chat_id:
            error_msg = await ask_message.reply_text(
                "<b>Pesan tidak valid! Harap teruskan pesan dari Database Channel.</b>",
                quote=True,
            )
            await client.delete_messages(chat_id, [ask_message.id, error_msg.id])
            return None

        # Hapus prompt begitu berhasil
        await client.delete_messages(chat_id, ask_message.id)
        return ask_message.forward_from_message_id

    prompt_messages = []

    # Step 1: Pesan Pertama
    first_message_id = await ask_for_message_id("Pesan Pertama", prompt_messages)
    if first_message_id is None:
        return

    # Step 2: Pesan Terakhir
    last_message_id = await ask_for_message_id("Pesan Terakhir", prompt_messages)
    if last_message_id is None:
        return

    # Generate encoded link
    try:
        first_id = first_message_id * abs(database_chat_id)
        last_id = last_message_id * abs(database_chat_id)
        encoded_data = url_safe.encode_data(f"id-{first_id}-{last_id}")
        encoded_data_url = f"https://t.me/{client.me.username}?start={encoded_data}"
        share_encoded_data_url = f"https://t.me/share?url={encoded_data_url}"

        await message.reply_text(
            f"<b>Berikut link batch Anda:</b>\n\n{encoded_data_url}",
            quote=True,
            reply_markup=ikb([[("🔗 Share", share_encoded_data_url, "url")]]),
            disable_web_page_preview=True,
        )

    except Exception as exc:
        logger.error(f"Batch: {exc}")
        error_msg = await message.reply_text("<b>Terjadi kesalahan saat membuat link batch!</b>", quote=True)
        await asyncio.sleep(3)
        await client.delete_messages(chat_id, error_msg.id)


# Callback handler untuk tombol Cancel
@Client.on_callback_query(filters.regex(r"^cancel_batch_\d+"))
async def cancel_batch(client: Client, callback_query):
    user_id = int(callback_query.data.split("_")[-1])

    if callback_query.from_user.id != user_id:
        await callback_query.answer("Bukan untukmu!", show_alert=True)
        return

    await callback_query.answer("❌ Proses dibatalkan.")

    # Edit pesan jadi notif batal
    await client.edit_message_text(
        chat_id=callback_query.message.chat.id,
        message_id=callback_query.message.id,
        text="❌ Proses telah dibatalkan oleh pengguna."
    )
    await asyncio.sleep(3)
    await client.delete_messages(callback_query.message.chat.id, callback_query.message.id)

    # Kirim pesan "CANCELLED" supaya ask() terpicu batal
    await client.send_message(
        chat_id=callback_query.message.chat.id,
        text="CANCELLED"
    )

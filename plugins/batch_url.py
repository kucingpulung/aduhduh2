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

    async def ask_for_message_id(ask_msg: str) -> int:
        """
        Ask the user to forward a message from the Database Channel and return the message ID.
        """
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
        except errors.ListenerTimeout:
            await message.reply_text("<b>Waktu habis! Proses dibatalkan.</b>")
            return None

        # Check if user clicked cancel (via callback handler, see below)
        if ask_message.text == "CANCELLED":
            await message.reply_text("<b>Proses batch telah dibatalkan oleh pengguna.</b>")
            return None

        if not ask_message.forward_from_chat or ask_message.forward_from_chat.id != database_chat_id:
            await ask_message.reply_text(
                "<b>Pesan tidak valid! Harap teruskan pesan dari Database Channel.</b>",
                quote=True,
            )
            return None

        return ask_message.forward_from_message_id

    # Ask for the first message
    first_message_id = await ask_for_message_id("Pesan Pertama")
    if first_message_id is None:
        return

    # Ask for the last message
    last_message_id = await ask_for_message_id("Pesan Terakhir")
    if last_message_id is None:
        return

    # Encode data and generate link
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
        await message.reply_text("<b>Terjadi kesalahan saat membuat link batch!</b>", quote=True)


# Callback handler for cancel button
@Client.on_callback_query(filters.regex(r"^cancel_batch_\d+"))
async def cancel_batch(client: Client, callback_query):
    user_id = int(callback_query.data.split("_")[-1])

    if callback_query.from_user.id != user_id:
        await callback_query.answer("Bukan untukmu!", show_alert=True)
        return

    await callback_query.answer("❌ Proses dibatalkan.")

    # Send a fake message back to the ask() waiter
    await client.send_message(
        chat_id=callback_query.message.chat.id,
        text="CANCELLED"
    )

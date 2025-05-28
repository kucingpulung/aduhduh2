from hydrogram import Client, errors, filters
from hydrogram.helpers import ikb
from hydrogram.types import Message

from bot import authorized_users_only, config, logger, url_safe


@Client.on_message(filters.private & filters.command("batch"))
@authorized_users_only
async def batch_handler(client: Client, message: Message) -> None:
    database_chat_id = config.DATABASE_CHAT_ID
    database_ch_link = f"tg://openmessage?chat_id={str(database_chat_id)[4:]}"  # 🔥 PINDAH KE SINI

    async def ask_for_message_id(ask_msg: str) -> int:
        chat_id, user_id = message.chat.id, message.from_user.id

        try:
            ask_message = await client.ask(
                chat_id=chat_id,
                text=(
                    f"<b>{ask_msg}:</b>\n"
                    f"Silakan teruskan pesan dari <a href='{database_ch_link}'>Database Channel</a>!\n\n"
                    f"<b>Timeout:</b> 45 detik"
                ),
                user_id=user_id,
                timeout=45,
                reply_markup=ikb([[("📂 Buka Database Channel", database_ch_link, "url")]]),
            )
        except errors.ListenerTimeout:
            await message.reply_text(
                "<b>Batas waktu habis! Proses dibatalkan.</b>"
            )
            return None

        if (
            not ask_message.forward_from_chat
            or ask_message.forward_from_chat.id != database_chat_id
        ):
            await ask_message.reply_text(
                "<b>Pesan tidak valid! Harap teruskan pesan dari Database Channel.</b>",
                quote=True,
            )
            return None

        return ask_message.forward_from_message_id

    # Get the start and end message IDs
    first_message_id = await ask_for_message_id("Awal Pesan Batch")
    if first_message_id is None:
        return

    last_message_id = await ask_for_message_id("Akhir Pesan Batch")
    if last_message_id is None:
        return

    # Encode data
    try:
        first_id = first_message_id * abs(database_chat_id)
        last_id = last_message_id * abs(database_chat_id)
        encoded_data = url_safe.encode_data(f"id-{first_id}-{last_id}")
        encoded_data_url = f"https://t.me/{client.me.username}?start={encoded_data}"
        share_encoded_data_url = f"https://t.me/share?url={encoded_data_url}"

        # Send the response
        await message.reply_text(
            encoded_data_url,
            quote=True,
            reply_markup=ikb([
                [("📂 Buka Database Channel", database_ch_link, "url")],
                [("🔗 Bagikan", share_encoded_data_url, "url")]
            ]),
            disable_web_page_preview=True,
        )
    except Exception as exc:
        logger.error(f"Batch: {exc}")
        await message.reply_text("<b>Terjadi kesalahan!</b>", quote=True)

import asyncio
from hydrogram import Client, errors, filters
from hydrogram.helpers import ikb
from hydrogram.types import Message
from hydrogram.errors import MessageNotModified

from bot import authorized_users_only, config, logger, url_safe

@Client.on_message(filters.private & filters.command("batch"))
@authorized_users_only
async def batch_handler(client: Client, message: Message) -> None:
    database_chat_id = config.DATABASE_CHAT_ID

    async def ask_for_message_id(ask_msg: str) -> int:
        """
        Meminta pengguna untuk meneruskan pesan dari Database Channel dan mengembalikan message_id-nya.
        """
        database_ch_link = f"https://t.me/c/{str(database_chat_id)[4:]}"
        chat_id, user_id = message.chat.id, message.from_user.id
        timeout = 45

        text_template = (
            f"<b>{ask_msg}:</b>\n"
            f"Silakan teruskan pesan dari <a href=\"{database_ch_link}\">Database Channel</a>!\n\n"
            f"<b>Sisa waktu:</b> {{seconds}} detik"
        )

        sent_message = await message.reply_text(
            text_template.format(seconds=timeout),
            disable_web_page_preview=True,
            reply_markup=ikb([[("Buka Database Channel 📂", database_ch_link, "url")]]),
        )

        async def countdown_updater():
            nonlocal timeout
            while timeout > 0:
                await asyncio.sleep(1)
                timeout -= 1
                try:
                    await sent_message.edit_text(
                        text_template.format(seconds=timeout),
                        disable_web_page_preview=True,
                        reply_markup=ikb([[("Buka Database Channel 📂", database_ch_link, "url")]]),
                    )
                except MessageNotModified:
                    pass  # Abaikan jika teks tidak berubah

        updater_task = asyncio.create_task(countdown_updater())

        try:
            ask_message = await client.ask(
                chat_id=chat_id,
                text=None,  # Kita sudah kirim pesan manual
                user_id=user_id,
                timeout=timeout,
            )
            updater_task.cancel()
        except errors.ListenerTimeout:
            updater_task.cancel()
            await sent_message.edit_text(
                "<b>Batas waktu habis! Proses telah dibatalkan.</b>"
            )
            return None

        if (
            not ask_message.forward_from_chat
            or ask_message.forward_from_chat.id != database_chat_id
        ):
            await ask_message.reply_text(
                "<b>Pesan tidak valid! Harap teruskan pesan dari Database Channel yang benar.</b>",
                quote=True,
            )
            return None

        return ask_message.forward_from_message_id

    # Ambil ID pesan awal
    first_message_id = await ask_for_message_id("Mulai")
    if first_message_id is None:
        return

    # Ambil ID pesan akhir
    last_message_id = await ask_for_message_id("Selesai")
    if last_message_id is None:
        return

    # Encode data
    try:
        first_id = first_message_id * abs(database_chat_id)
        last_id = last_message_id * abs(database_chat_id)
        encoded_data = url_safe.encode_data(f"id-{first_id}-{last_id}")
        encoded_data_url = f"https://t.me/{client.me.username}?start={encoded_data}"
        share_encoded_data_url = f"https://t.me/share?url={encoded_data_url}"

        await message.reply_text(
            f"<b>Berhasil!</b>\nBerikut adalah link batch Anda:\n\n<code>{encoded_data_url}</code>",
            quote=True,
            reply_markup=ikb([[("Bagikan 🔗", share_encoded_data_url, "url")]]),
            disable_web_page_preview=True,
        )
    except Exception as exc:
        logger.error(f"Batch: {exc}")
        await message.reply_text("<b>Terjadi kesalahan!</b>", quote=True)

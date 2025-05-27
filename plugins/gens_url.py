from hydrogram import Client, filters
from hydrogram.helpers import ikb
from hydrogram.types import Message

from bot import authorized_users_only, config, helper_handlers, logger, url_safe
from plugins import list_available_commands


@Client.on_message(
    filters.private & ~filters.me & ~filters.command(list_available_commands)
)
@authorized_users_only
async def generate_handler(client: Client, message: Message) -> None:
    # Check generate status
    if not helper_handlers.generate_status:
        return

    try:
        # === VARIABEL UNTUK GANTI CAPTION ===
        # Ubah ini sesuai kebutuhanmu. "0" artinya tetap pakai caption asli.
        custom_caption = "ini caption contoh!!"  # atau bisa diganti "Teks caption baru dari admin"

        # Tentukan caption yang akan digunakan
        caption_to_use = message.caption if custom_caption == "0" else custom_caption

        # ID chat database
        database_chat_id = config.DATABASE_CHAT_ID

        # === SALIN PESAN DENGAN/ TANPA CAPTION BARU ===
        if message.photo:
            message_db = await client.send_photo(
                chat_id=database_chat_id,
                photo=message.photo.file_id,
                caption=caption_to_use
            )
        elif message.document:
            message_db = await client.send_document(
                chat_id=database_chat_id,
                document=message.document.file_id,
                caption=caption_to_use
            )
        elif message.video:
            message_db = await client.send_video(
                chat_id=database_chat_id,
                video=message.video.file_id,
                caption=caption_to_use
            )
        elif message.audio:
            message_db = await client.send_audio(
                chat_id=database_chat_id,
                audio=message.audio.file_id,
                caption=caption_to_use
            )
        elif message.text:
            message_db = await client.send_message(
                chat_id=database_chat_id,
                text=caption_to_use
            )
        else:
            # Fallback kalau jenis pesan tidak dikenal
            message_db = await message.copy(database_chat_id)

        # === BUAT LINK UNIK ===
        encoded_data = url_safe.encode_data(
            f"id-{message_db.id * abs(database_chat_id)}"
        )
        encoded_data_url = f"https://t.me/{client.me.username}?start={encoded_data}"
        share_encoded_data_url = f"https://t.me/share/url?url={encoded_data_url}"

        # Balas ke user dengan link
        await message.reply_text(
            encoded_data_url,
            quote=True,
            reply_markup=ikb([[("Share", share_encoded_data_url, "url")]]),
            disable_web_page_preview=True,
        )

    except Exception as exc:
        # Tangani error
        logger.error(f"Generator: {exc}")
        await message.reply_text("<b>An Error Occurred!</b>", quote=True)

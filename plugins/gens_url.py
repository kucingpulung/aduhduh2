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
    if not helper_handlers.generate_status:
        return

    try:
        # === VARIABEL SETTING MANUAL ===
        db_caption = "asupan mantap"  # "0" untuk pakai caption original
        konten_caption = 'Download media <a href="{link}">disini</a>'
        konten_chat_id = -1002573263047
        database_chat_id = config.DATABASE_CHAT_ID

        # Kirim ke database channel
        message_db = await message.copy(database_chat_id)

        # Generate link
        encoded_data = url_safe.encode_data(
            f"id-{message_db.id * abs(database_chat_id)}"
        )
        encoded_data_url = f"https://t.me/{client.me.username}?start={encoded_data}"
        share_encoded_data_url = f"https://t.me/share/url?url={encoded_data_url}"

        # === ATUR CAPTION DB DAN KONTEN ===
        original_caption = message.caption or ""
        final_db_caption = original_caption if db_caption == "0" else db_caption.replace("{link}", encoded_data_url)
        final_konten_caption = konten_caption.replace("{link}", encoded_data_url)

        # Kirim ke konten channel
        if message.photo:
            konten_msg = await client.send_photo(
                konten_chat_id,
                photo=message.photo.file_id,
                caption=final_konten_caption,
                parse_mode="HTML"
            )
        elif message.document:
            konten_msg = await client.send_document(
                konten_chat_id,
                document=message.document.file_id,
                caption=final_konten_caption,
                parse_mode="HTML"
            )
        elif message.video:
            konten_msg = await client.send_video(
                konten_chat_id,
                video=message.video.file_id,
                caption=final_konten_caption,
                parse_mode="HTML"
            )
        elif message.audio:
            konten_msg = await client.send_audio(
                konten_chat_id,
                audio=message.audio.file_id,
                caption=final_konten_caption,
                parse_mode="HTML"
            )
        elif message.text:
            konten_msg = await client.send_message(
                konten_chat_id,
                text=final_konten_caption,
                parse_mode="HTML"
            )
        else:
            konten_msg = await message.copy(konten_chat_id)

        # URL postingan
        konten_url = f"https://t.me/c/{str(konten_chat_id)[4:]}/{konten_msg.id}"
        db_url = f"https://t.me/c/{str(database_chat_id)[4:]}/{message_db.id}"

        # Tampilkan ke user
        await message.reply_text(
            final_db_caption,
            quote=True,
            parse_mode="HTML",
            reply_markup=ikb([
                [("Share", share_encoded_data_url, "url")],
                [("Lihat Konten", konten_url, "url")],
                [("Lihat DB", db_url, "url")]
            ]),
            disable_web_page_preview=True,
        )

    except Exception as exc:
        logger.error(f"Generator: {exc}")
        await message.reply_text("<b>An Error Occurred!</b>", quote=True)

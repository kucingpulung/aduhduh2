import asyncio
from hydrogram import Client, errors, filters
from hydrogram.helpers import ikb
from hydrogram.types import Message

from bot import authorized_users_only, config, logger, url_safe

@Client.on_message(filters.private & filters.command("batch"))
@authorized_users_only
async def batch_handler(client: Client, message: Message) -> None:
    database_chat_id = config.DATABASE_CHAT_ID

    async def ask_for_message_id(ask_msg: str) -> int:
        database_ch_link = f"tg://openmessage?chat_id={str(database_chat_id)[4:]}"
        chat_id, user_id = message.chat.id, message.from_user.id

        timeout = 60  # 1 minute timeout
        emojis = ["⏳", "⌛"]  # jam pasir penuh dan kosong

        # Initial loading message (no buttons)
        prompt_message = await message.reply_text(
            f"<b>{ask_msg}</b>\n⏳ [▓▓▓▓▓▓▓▓▓▓] {timeout}s\nForward a message from the Database Channel!"
        )

        countdown_task = asyncio.create_task(
            countdown_timer(prompt_message, timeout, ask_msg, emojis)
        )

        try:
            # Main prompt (with button)
            ask_message = await client.ask(
                chat_id=chat_id,
                text=f"<b>{ask_msg}:</b>\nForward a message from the Database Channel!\n\n<b>Timeout:</b> {timeout}s",
                user_id=user_id,
                timeout=timeout,
                reply_markup=ikb([[("Database Channel", database_ch_link, "url")]]),
            )
            countdown_task.cancel()
        except errors.ListenerTimeout:
            countdown_task.cancel()
            await prompt_message.edit_text(
                "<b>⏳ Time limit exceeded! Process has been cancelled.</b>"
            )
            return None

        if (
            not ask_message.forward_from_chat
            or ask_message.forward_from_chat.id != database_chat_id
        ):
            await ask_message.reply_text(
                "<b>Invalid message! Please forward a message from the Database Channel.</b>",
                quote=True,
            )
            return None

        return ask_message.forward_from_message_id

    async def countdown_timer(msg, total_seconds, ask_msg, emojis):
        bar_length = 10
        for remaining in range(total_seconds, 0, -1):
            filled_length = int(bar_length * remaining / total_seconds)
            bar = "▓" * filled_length + "░" * (bar_length - filled_length)
            emoji = emojis[remaining % len(emojis)]  # bergantian ⏳ ⌛
            try:
                await msg.edit_text(
                    f"<b>{ask_msg}</b>\n{emoji} [{bar}] {remaining}s\nForward a message from the Database Channel!"
                )
                await asyncio.sleep(1)
            except Exception:
                break  # stop if cancelled or fails

    try:
        first_message_id = await ask_for_message_id("Start")
        if first_message_id is None:
            return

        last_message_id = await ask_for_message_id("End")
        if last_message_id is None:
            return

        first_id = first_message_id * abs(database_chat_id)
        last_id = last_message_id * abs(database_chat_id)
        encoded_data = url_safe.encode_data(f"id-{first_id}-{last_id}")
        encoded_data_url = f"https://t.me/{client.me.username}?start={encoded_data}"
        share_encoded_data_url = f"https://t.me/share?url={encoded_data_url}"
        database_ch_link = f"tg://openmessage?chat_id={str(database_chat_id)[4:]}"

        await message.reply_text(
            encoded_data_url,
            quote=True,
            reply_markup=ikb([
                [("Database Channel", database_ch_link, "url")],
                [("Share", share_encoded_data_url, "url")]
            ]),
            disable_web_page_preview=True,
        )
    except Exception as exc:
        logger.error(f"Batch: {exc}")
        await message.reply_text("<b>An Error Occurred!</b>", quote=True)

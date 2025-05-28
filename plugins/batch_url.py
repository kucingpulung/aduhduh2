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

        # Separate message for loading bar (no button, safe to edit)
        prompt_message = await message.reply_text(
            f"<b>{ask_msg}</b>\n⏳ [▓▓▓▓▓▓▓▓▓▓] {timeout}s\nForward a message from the Database Channel!"
        )

        # Create stop flag
        stop_event = asyncio.Event()

        # Run countdown in background
        countdown_task = asyncio.create_task(
            countdown_timer(prompt_message, timeout, ask_msg, stop_event)
        )

        try:
            # Actual prompt with button
            ask_message = await asyncio.shield(
                client.ask(
                    chat_id=chat_id,
                    text=f"<b>{ask_msg}:</b>\nForward a message from the Database Channel!\n\n<b>Timeout:</b> {timeout}s",
                    user_id=user_id,
                    timeout=timeout,
                    reply_markup=ikb([[("Database Channel", database_ch_link, "url")]]),
                )
            )
            stop_event.set()  # stop countdown when answered
            await countdown_task  # wait for it to finish cleanly
        except errors.ListenerTimeout:
            stop_event.set()
            await countdown_task
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

    async def countdown_timer(msg, total_seconds, ask_msg, stop_event):
        bar_length = 10
        for remaining in range(total_seconds, 0, -1):
            if stop_event.is_set():
                break

            filled_length = int(bar_length * remaining / total_seconds)
            bar = "▓" * filled_length + "░" * (bar_length - filled_length)

            try:
                await msg.edit_text(
                    f"<b>{ask_msg}</b>\n⏳ [{bar}] {remaining}s\nForward a message from the Database Channel!"
                )
            except Exception as e:
                logger.warning(f"Countdown edit failed: {e}")
                break  # stop if edit fails

            await asyncio.sleep(1)

    # Get the start and end message IDs
    first_message_id = await ask_for_message_id("Start")
    if first_message_id is None:
        return

    last_message_id = await ask_for_message_id("End")
    if last_message_id is None:
        return

    try:
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

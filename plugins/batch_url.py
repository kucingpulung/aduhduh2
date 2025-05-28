from hydrogram import Client, errors, filters
from hydrogram.helpers import ikb
from hydrogram.types import Message, CallbackQuery

from bot import authorized_users_only, config, logger, url_safe


active_cancellations = set()


@Client.on_message(filters.private & filters.command("batch"))
@authorized_users_only
async def batch_handler(client: Client, message: Message) -> None:
    database_chat_id = config.DATABASE_CHAT_ID
    user_id = message.from_user.id

    async def ask_for_message_id(ask_msg: str) -> int:
        database_ch_link = f"tg://openmessage?chat_id={str(database_chat_id)[4:]}"
        chat_id = message.chat.id

        prompt_message = await message.reply(
            text=f"<b>{ask_msg}:</b>\nForward a message from the Database Channel!\n\n<b>Timeout:</b> 45s",
            reply_markup=ikb([
                [("Database Channel", database_ch_link, "url")],
                [("❌ Cancel", f"cancel_batch_{user_id}")]
            ]),
        )

        try:
            user_response = await client.ask(
                chat_id=chat_id,
                user_id=user_id,
                timeout=45,
            )
        except errors.ListenerTimeout:
            await prompt_message.edit_text("<b>⏰ Time limit exceeded! Process has been cancelled.</b>")
            return None

        # Check if cancelled
        if user_id in active_cancellations:
            active_cancellations.remove(user_id)
            await prompt_message.edit_text("<b>❌ Process cancelled by user.</b>")
            return None

        if (
            not user_response.forward_from_chat
            or user_response.forward_from_chat.id != database_chat_id
        ):
            await user_response.reply_text(
                "<b>⚠ Invalid message! Please forward a message from the Database Channel.</b>",
                quote=True,
            )
            return None

        return user_response.forward_from_message_id

    # Start batch process: ask for first and second message IDs
    first_message_id = await ask_for_message_id("Start")
    if first_message_id is None:
        return

    last_message_id = await ask_for_message_id("End")
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
            f"<b>Your batch link:</b>\n{encoded_data_url}",
            quote=True,
            reply_markup=ikb([[("🔗 Share", share_encoded_data_url, "url")]]),
            disable_web_page_preview=True,
        )
    except Exception as exc:
        logger.error(f"Batch: {exc}")
        await message.reply_text("<b>❌ An Error Occurred!</b>", quote=True)


# === CALLBACK HANDLER UNTUK CANCEL ===
@Client.on_callback_query(filters.regex(r"cancel_batch_(\d+)"))
async def cancel_batch_handler(client: Client, callback_query: CallbackQuery):
    user_id = int(callback_query.matches[0].group(1))

    # Mark user as cancelled
    active_cancellations.add(user_id)

    try:
        await callback_query.message.edit_text("❌ Process cancelled by user.")
        await callback_query.answer("Batch process cancelled.")
        # Resolve listener to stop the ask wait
        await client.resolve_listener(user_id, None)
    except Exception as e:
        logger.error(f"Cancel Callback Error: {e}")
        await callback_query.answer("An error occurred cancelling the process.", show_alert=True)

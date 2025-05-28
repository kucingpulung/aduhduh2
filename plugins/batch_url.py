from hydrogram import Client, errors, filters
from hydrogram.helpers import ikb
from hydrogram.types import Message, CallbackQuery

from bot import authorized_users_only, config, logger, url_safe


@Client.on_message(filters.private & filters.command("batch"))
@authorized_users_only
async def batch_handler(client: Client, message: Message) -> None:
    database_chat_id = config.DATABASE_CHAT_ID

    async def ask_for_message_id(ask_msg: str) -> int:
        """
        Ask the user to forward a message from the Database Channel and return the message ID.

        Args:
            ask_msg (str): The prompt message to display to the user.

        Returns:
            int: The ID of the forwarded message, or None if invalid or not received.
        """
        database_ch_link = f"tg://openmessage?chat_id={str(database_chat_id)[4:]}"
        chat_id, user_id = message.chat.id, message.from_user.id

        # Send initial prompt with Cancel button
        prompt_message = await message.reply(
            text=f"<b>{ask_msg}:</b>\nForward a message from the Database Channel!\n\n<b>Timeout:</b> 45s",
            reply_markup=ikb([
                [("Database Channel", database_ch_link, "url")],
                [("❌ Cancel", "cancel_batch")]
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

        # Check if cancelled via callback
        if user_response is None:
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

    # Get the start and end message IDs
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
            encoded_data_url,
            quote=True,
            reply_markup=ikb([[("🔗 Share", share_encoded_data_url, "url")]]),
            disable_web_page_preview=True,
        )
    except Exception as exc:
        logger.error(f"Batch: {exc}")
        await message.reply_text("<b>❌ An Error Occurred!</b>", quote=True)


# === CALLBACK HANDLER UNTUK CANCEL ===
@Client.on_callback_query(filters.regex("cancel_batch"))
async def cancel_batch_handler(client: Client, callback_query: CallbackQuery):
    try:
        await callback_query.message.edit_text("❌ Process cancelled by user.")
        # Force stop any pending ask listener
        await client.resolve_listener(callback_query.from_user.id, None)
    except Exception as e:
        logger.error(f"Cancel Callback Error: {e}")
        await callback_query.answer("An error occurred cancelling the process.", show_alert=True)

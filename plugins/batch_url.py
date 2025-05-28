import asyncio
from hydrogram import Client, filters
from hydrogram.helpers import ikb
from hydrogram.types import Message, CallbackQuery

from bot import authorized_users_only, config, logger, url_safe

# Track prompt messages & cancel events
active_prompts = {}
cancel_events = {}

@Client.on_message(filters.private & filters.command("batch"))
@authorized_users_only
async def batch_handler(client: Client, message: Message) -> None:
    database_chat_id = config.DATABASE_CHAT_ID
    chat_id, user_id = message.chat.id, message.from_user.id

    # Prepare cancel event
    cancel_events[user_id] = asyncio.Event()

    async def ask_for_message_id(step_name: str) -> int:
        database_ch_link = f"tg://openmessage?chat_id={str(database_chat_id)[4:]}"
        cancel_data = f"cancel_batch_{user_id}"

        prompt = await message.reply_text(
            f"<b>{step_name}:</b>\nSilakan teruskan pesan dari Database Channel!",
            reply_markup=ikb([
                [("📂 Database Channel", database_ch_link, "url")],
                [("❌ Cancel", f"callback:{cancel_data}")]
            ])
        )
        active_prompts[user_id] = prompt.id

        while True:
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(client.listen(chat_id)),
                    asyncio.create_task(cancel_events[user_id].wait())
                ],
                return_when=asyncio.FIRST_COMPLETED
            )

            if cancel_events[user_id].is_set():
                await client.edit_message_text(
                    chat_id=chat_id,
                    message_id=prompt.id,
                    text="❌ Proses telah dibatalkan oleh pengguna."
                )
                await asyncio.sleep(3)
                await client.delete_messages(chat_id, prompt.id)
                active_prompts.pop(user_id, None)
                return None

            for task in done:
                user_msg = task.result()
                if user_msg.from_user.id != user_id:
                    continue

                if user_msg.forward_from_chat and user_msg.forward_from_chat.id == database_chat_id:
                    await client.delete_messages(chat_id, prompt.id)
                    active_prompts.pop(user_id, None)
                    return user_msg.forward_from_message_id
                else:
                    warn_msg = await user_msg.reply_text("❗ Harap teruskan pesan dari Database Channel.")
                    await asyncio.sleep(3)
                    await client.delete_messages(chat_id, [warn_msg.id, user_msg.id])

    try:
        # Step 1
        first_message_id = await ask_for_message_id("Pesan Pertama")
        if first_message_id is None:
            return

        # Step 2
        last_message_id = await ask_for_message_id("Pesan Terakhir")
        if last_message_id is None:
            return

        # Generate batch link
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
        error_msg = await message.reply_text("<b>Terjadi kesalahan saat membuat link batch!</b>")
        await asyncio.sleep(3)
        await client.delete_messages(chat_id, error_msg.id)
    finally:
        # Cleanup
        cancel_events.pop(user_id, None)
        active_prompts.pop(user_id, None)

@Client.on_callback_query(filters.regex(r"^cancel_batch_\d+"))
async def cancel_batch(client: Client, callback_query: CallbackQuery):
    user_id = int(callback_query.data.split("_")[-1])

    if callback_query.from_user.id != user_id:
        await callback_query.answer("❌ Bukan untukmu!", show_alert=True)
        return

    await callback_query.answer("❌ Proses dibatalkan.")

    # Set cancel event
    if user_id in cancel_events:
        cancel_events[user_id].set()

    chat_id = callback_query.message.chat.id

    if user_id in active_prompts:
        try:
            await client.edit_message_text(
                chat_id=chat_id,
                message_id=active_prompts[user_id],
                text="❌ Proses telah dibatalkan oleh pengguna."
            )
            await asyncio.sleep(3)
            await client.delete_messages(chat_id, active_prompts[user_id])
        except Exception as e:
            logger.error(f"Error saat menghapus prompt: {e}")
        active_prompts.pop(user_id, None)

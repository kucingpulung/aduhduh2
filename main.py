import asyncio
import os
from hydrogram import errors
from hydrogram.helpers import ikb

from bot import (
    ForceStopLoop,
    bot,
    config,
    del_broadcast_data_id,
    get_broadcast_data_ids,
    helper_buttons,
    helper_handlers,
    initial_database,
    logger,
)

from http_server import HTTPServer  # Import HTTP server

async def chat_db_init() -> None:
    chat_id = config.DATABASE_CHAT_ID
    try:
        me = await bot.get_chat_member(chat_id, "me")
        if not me.privileges.can_post_messages:
            raise ForceStopLoop("ChatDB: No Privilege")
        else:
            logger.info(f"ChatDB: {chat_id}")
    except errors.RPCError as rpc:
        raise ForceStopLoop(f"ChatDB: {rpc.MESSAGE}")

async def send_msg_to_admins(msg_text: str, only_owner: bool = False) -> None:
    bot_admins = helper_handlers.admins
    own_button = ikb(helper_buttons.Contact)

    if only_owner:
        bot_admins = [config.OWNER_ID]
        own_button = None

    for admin in bot_admins:
        try:
            await bot.send_message(admin, msg_text, reply_markup=own_button)
            await asyncio.sleep(1.5)  # Anti-flood delay
        except errors.RPCError as e:
            logger.warning(f"Failed to message admin {admin}: {e}")

async def send_restart_msg(chat_id: int, message_id: int, text: str) -> None:
    try:
        await bot.send_message(chat_id, text, reply_to_message_id=message_id)
    except errors.RPCError as e:
        logger.warning(f"Failed to send restart message: {e}")

async def cache_db_init() -> None:
    await asyncio.gather(
        helper_handlers.force_text_init(),
        helper_handlers.start_text_init(),
        helper_handlers.generate_status_init(),
        helper_handlers.protect_content_init(),
        helper_handlers.admins_init(),
        helper_handlers.fs_chats_init(),
    )

async def restart_data_init() -> None:
    try:
        chat_id, message_id = await get_broadcast_data_ids()
        logger.info(f"BroadcastID: {chat_id}, {message_id}")

        if chat_id and message_id:
            await send_restart_msg(chat_id, message_id, "<b>An Error Occurred!</b>")
            await del_broadcast_data_id()

        task_msg = (
            "<u><b>Bot Up and Running!</b></u>\n\n"
            "  <b>Broadcast Status</b>\n"
            f"    - <code>Chat ID:</code> {chat_id}\n"
            f"    - <code>Msg ID :</code> {message_id}"
        )
        await send_msg_to_admins(task_msg, only_owner=True)

    except Exception as exc:
        logger.error(f"Restart Init Error: {exc}")

async def main() -> None:
    await bot.start()
    bot_user_id, bot_username = bot.me.id, bot.me.username

    await initial_database()
    await chat_db_init()
    await cache_db_init()
    await restart_data_init()

    logger.info(f"@{bot_username} {bot_user_id}")

    # HTTP server init (for Koyeb or health checks)
    port = int(os.environ.get("PORT", 8080))
    http_server = HTTPServer("0.0.0.0", port)
    asyncio.create_task(http_server.run_server())

    logger.info(f"HTTP server running on port {port}")

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(main())
        logger.info("Bot Activated!")
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt: Terminating...")
    except ForceStopLoop as fsl:
        logger.error(str(fsl))
    finally:
        logger.info("Bot: Stopping...")
        loop.run_until_complete(bot.stop())
        loop.close()

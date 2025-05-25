import asyncio
import logging

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

# =========================
# HTTP SERVER UNTUK HEALTH CHECK
# =========================
class HTTPServer:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port

    async def handle_request(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        try:
            request = await reader.read(1024)
            if not request:
                return

            path = request.decode().split(" ")[1]
            if path == "/":
                response = (
                    "HTTP/1.1 200 OK\r\n"
                    "Content-Type: text/html\r\n\r\n"
                    "<h1>Bot is running</h1>"
                )
            else:
                response = (
                    "HTTP/1.1 404 Not Found\r\n"
                    "Content-Type: text/html\r\n\r\n"
                    "<h1>404 Not Found</h1>"
                )

            writer.write(response.encode())
            await writer.drain()
        finally:
            writer.close()
            await writer.wait_closed()

    async def run_server(self):
        server = await asyncio.start_server(self.handle_request, self.host, self.port)
        logger.info(f"HTTP Server running at http://{self.host}:{self.port}")
        async with server:
            await server.serve_forever()

# =========================
# BOT INITIALIZATION
# =========================

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
        except errors.RPCError:
            continue

async def send_restart_msg(chat_id: int, message_id: int, text: str) -> None:
    await bot.send_message(chat_id, text, reply_to_message_id=message_id)

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
        logger.error(str(exc))

# =========================
# MAIN FUNCTION
# =========================

async def main() -> None:
    await bot.start()
    bot_user_id, bot_username = bot.me.id, bot.me.username

    await initial_database()
    await chat_db_init()
    await cache_db_init()
    await restart_data_init()

    # Jalankan HTTP server tanpa menghentikan bot
    server = HTTPServer("0.0.0.0", 8000)
    asyncio.create_task(server.run_server())

    logger.info(f"Bot started as @{bot_username} ({bot_user_id})")

# =========================
# ENTRY POINT
# =========================

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

import time
import datetime

from hydrogram import Client, filters
from hydrogram.helpers import ikb
from hydrogram.raw import functions
from hydrogram.types import CallbackQuery, Message

from bot import helper_buttons, logger

# Catat waktu saat bot mulai jalan
startup_time = datetime.datetime.now()


@Client.on_message(filters.private & filters.command("ping"))
async def ping_handler(client: Client, message: Message) -> None:
    try:
        latency = await ping_function(client)
        uptime = get_full_uptime()
        await message.reply_text(
            f"<b>Latency:</b> {latency}\n\n{uptime}",
            quote=True,
            reply_markup=ikb(helper_buttons.Ping),
        )
    except Exception as exc:
        logger.error(f"Ping/Uptime Error: {exc}")
        await message.reply_text("<b>An Error Occurred!</b>", quote=True)


@Client.on_callback_query(filters.regex(r"\bping\b"))
async def ping_handler_query(client: Client, query: CallbackQuery) -> None:
    await query.message.edit_text("<b>Refreshing...</b>")

    try:
        latency = await ping_function(client)
        uptime = get_full_uptime()
        await query.message.edit_text(
            f"<b>Latency:</b> {latency}\n\n{uptime}",
            reply_markup=ikb(helper_buttons.Ping),
        )
    except Exception as exc:
        logger.error(f"Ping/Uptime Callback Error: {exc}")
        await query.message.edit_text(
            "<b>An Error Occurred!</b>", reply_markup=ikb(helper_buttons.Ping)
        )


async def ping_function(client: Client) -> str:
    start_time = time.time()
    await client.invoke(functions.Ping(ping_id=0))
    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000
    return f"{latency_ms:.2f} ms"


def get_full_uptime() -> str:
    now = datetime.datetime.now()
    total_seconds = (now - startup_time).total_seconds()

    since_str = startup_time.strftime("%B %d, %Y at %I:%M %p")

    weeks, remainder = divmod(total_seconds, 604800)
    days, remainder = divmod(remainder, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    duration_parts = []
    if weeks: duration_parts.append(f"{int(weeks)} Week{'s' if weeks > 1 else ''}")
    if days: duration_parts.append(f"{int(days)} Day{'s' if days > 1 else ''}")
    if hours: duration_parts.append(f"{int(hours)} Hour{'s' if hours > 1 else ''}")
    if minutes: duration_parts.append(f"{int(minutes)} Minute{'s' if minutes > 1 else ''}")
    if seconds: duration_parts.append(f"{int(seconds)} Second{'s' if seconds > 1 else ''}")

    duration_str = ", ".join(duration_parts[:5])  # maksimal 3 komponen

    return (
        "<b>Uptime:</b>\n"
        f"  - <code>Since:</code> {since_str}\n"
        f"  - <code>Total:</code> {duration_str}"
    )

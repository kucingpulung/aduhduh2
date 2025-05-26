import time
import datetime

from hydrogram import Client, filters
from hydrogram.helpers import ikb
from hydrogram.raw import functions
from hydrogram.types import CallbackQuery, Message

from bot import helper_buttons, logger

# Tanda waktu saat bot mulai
startup_time = datetime.datetime.now()


async def ping_function(client: Client) -> str:
    start = time.time()
    await client.invoke(functions.Ping(ping_id=0))
    return f"{(time.time() - start)*1000:.2f} ms"


def get_full_uptime() -> str:
    now = datetime.datetime.now()
    total = (now - startup_time).total_seconds()
    # Hitung komponen waktu
    weeks, rem = divmod(total, 604800)
    days, rem = divmod(rem, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)

    since = startup_time.strftime("%B %d, %Y at %I:%M %p")
    parts = []
    if weeks:   parts.append(f"{int(weeks)} Week{'s' if weeks>1 else ''}")
    if days:    parts.append(f"{int(days)} Day{'s' if days>1 else ''}")
    if hours:   parts.append(f"{int(hours)} Hour{'s' if hours>1 else ''}")
    if minutes: parts.append(f"{int(minutes)} Minute{'s' if minutes>1 else ''}")
    if seconds: parts.append(f"{int(seconds)} Second{'s' if seconds>1 else ''}")
    total_str = ", ".join(parts[:3])  # maksimal 3 komponen

    # Bentuk teks HTML
    return (
        f"<b>Uptime Since</b>\n"
        f"<code>{since}</code>\n\n"
        f"<b>Uptime Total</b>\n"
        f"<code>{total_str}</code>"
    )


@Client.on_message(filters.private & filters.command("ping"))
async def ping_handler(client: Client, message: Message) -> None:
    try:
        latency = await ping_function(client)
        uptime  = get_full_uptime()
        text = (
            f"<b>Latency</b>\n"
            f"<code>{latency}</code>\n\n"
            f"{uptime}"
        )
        await message.reply_text(
            text,
            parse_mode="HTML",
            quote=True,
            reply_markup=ikb(helper_buttons.Ping),
            disable_web_page_preview=True,
        )
    except Exception as exc:
        logger.error(f"Ping/Uptime Error: {exc}")
        await message.reply_text("<b>An Error Occurred!</b>", parse_mode="HTML", quote=True)


@Client.on_callback_query(filters.regex(r"\bping\b"))
async def ping_callback(client: Client, query: CallbackQuery) -> None:
    await query.answer()  # optional ack
    await query.message.edit_text("<b>Refreshing…</b>", parse_mode="HTML")

    try:
        latency = await ping_function(client)
        uptime  = get_full_uptime()
        text = (
            f"<b>Latency</b>\n"
            f"<code>{latency}</code>\n\n"
            f"{uptime}"
        )
        await query.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=ikb(helper_buttons.Ping),
            disable_web_page_preview=True,
        )
    except Exception as exc:
        logger.error(f"Ping/Uptime Callback Error: {exc}")
        await query.message.edit_text("<b>An Error Occurred!</b>", parse_mode="HTML")

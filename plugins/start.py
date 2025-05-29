import json  
import os  
from hydrogram import Client, errors, filters  
from hydrogram.types import Message, User

SPONSOR_FILE = "sponsor.json"

def load_sponsor(): if os.path.exists(SPONSOR_FILE): with open(SPONSOR_FILE, "r") as f: data = json.load(f) return data.get("message_id") return None

def save_sponsor(message_id): with open(SPONSOR_FILE, "w") as f: json.dump({"message_id": message_id}, f)

def clear_sponsor(): if os.path.exists(SPONSOR_FILE): os.remove(SPONSOR_FILE)

@Client.on_message(filters.private & filters.command("start")) async def start_handler(client: Client, message: Message) -> None: user = message.from_user await add_user(user.id)

start_text = format_text_message(helper_handlers.start_text, user)
user_buttons = await join_buttons(client, message, user.id)
if len(message.command) == 1:
    buttons = admin_buttons() if user.id in helper_handlers.admins else user_buttons
    await message.reply_text(start_text, quote=True, reply_markup=buttons)
else:
    force_text = format_text_message(helper_handlers.force_text, user)
    if await helper_handlers.user_is_not_join(user.id):
        await message.reply_text(force_text, quote=True, reply_markup=user_buttons)
        return

    try:
        message_ids = helper_handlers.decode_data(message.command[1])
        msgs = await client.get_messages(config.DATABASE_CHAT_ID, message_ids)
        for msg in msgs:
            if not msg.empty:
                await msg.copy(
                    user.id, protect_content=helper_handlers.protect_content
                )

        sponsor_id = load_sponsor()
        if sponsor_id:
            try:
                sponsor_msg = await client.get_messages(config.DATABASE_CHAT_ID, sponsor_id)
                if sponsor_msg:
                    await sponsor_msg.copy(user.id)
            except errors.RPCError:
                pass
    except errors.RPCError:
        pass

@Client.on_message(filters.private & filters.command("privacy")) async def privacy_handler(client: Client, message: Message) -> None: privacy_policy = f""" <b>Privacy Policy for {client.me.first_name.title()}</b> <b>Last Updated: July 04, 2024</b>

This Privacy Policy explains how we collect, use, and protect your information when you use our bot.

<b>1. Information We Collect</b>

<blockquote><b>1.1 Personal Information</b>
- We do not collect any personal information such as your name, email address, or phone number.<b>1.2 Usage Data</b>

We may collect information about your interactions with the bot, such as messages sent, commands used, and the time and date of your interactions.</blockquote>


<b>2. How We Use Your Information</b>

<blockquote><b>2.1 To Operate the Bot</b>
- The information collected is used to operate and improve the functionality of the bot.<b>2.2 To Improve Our Services</b>

We may use the information to analyze how users interact with the bot in order to improve our services.</blockquote>


<b>3. Data Security</b>

<blockquote><b>3.1 Security Measures</b>
- We implement appropriate technical and organizational measures to protect your information from unauthorized access, disclosure, alteration, or destruction.</blockquote><b>4. Data Sharing and Disclosure</b>

<blockquote><b>4.1 Third-Party Services</b>
- We do not share your information with third parties, except as required by law or to protect our rights.</blockquote><b>5. Your Data Protection Rights</b>

<blockquote><b>5.1 Access and Control</b>
- You have the right to request access to the information we have collected about you. You also have the right to request that we correct or delete your data.</blockquote><b>6. Changes to This Privacy Policy</b>

<blockquote><b>6.1 Updates</b>
- We may update our Privacy Policy from time to time. We will notify you of any changes by posting the new Privacy Policy on this page.</blockquote><b>7. Contact Us</b>

<blockquote><b>7.1 Contact Information</b>
- If you have any questions about this Privacy Policy, please contact us on the button below.</blockquote><b>Note:</b>

<blockquote>- It's important to review this policy with a legal professional to ensure compliance with relevant laws and regulations.</blockquote>
"""await message.reply_text(
    privacy_policy, quote=True, reply_markup=ikb(helper_buttons.Contact)
)

def format_text_message(text: str, user: User) -> str: first_name, last_name = user.first_name, user.last_name full_name = f"{first_name} {last_name}".strip() if last_name else first_name

return text.format(
    first_name=first_name,
    last_name=last_name,
    full_name=full_name,
    mention=user.mention(full_name),
)

@Client.on_message(filters.private & filters.command("sponsor")) async def sponsor_handler(client: Client, message: Message) -> None: user = message.from_user if user.id not in helper_handlers.admins: await message.reply_text("❌ Only admins can set sponsor messages.") return

if len(message.command) == 1:
    await message.reply_text("✅ Please reply to the sponsor message from the database channel and forward it here, or use /sponsor off to remove it.")
elif message.command[1].lower() == "off":
    clear_sponsor()
    await message.reply_text("✅ Sponsor message removed.")
elif message.reply_to_message:
    sponsor_msg_id = message.reply_to_message.forward_from_message_id
    if sponsor_msg_id:
        save_sponsor(sponsor_msg_id)
        await message.reply_text("✅ Sponsor message set.")
    else:
        await message.reply_text("❌ Please forward the sponsor message from the database channel.")


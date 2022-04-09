from telethon import TelegramClient, events
from telethon.tl.types import InputChannel
from googletrans import Translator
from switches import get_chat_name, get_flag
import logging
import yaml
import os
import re

# Logging as per docs
logging.basicConfig(format='[%(levelname) 5s/%(asctime)s] %(name)s: %(message)s', level=logging.WARNING)
logging.getLogger('telethon').setLevel(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Set config values
api_id = os.environ.get('api_id')
api_hash = os.environ.get('api_hash')
phone = os.environ.get('phone')
username = os.environ.get('username')
channel_link = os.environ.get('channel_link')

with open('config.yml', 'rb') as f:
    config = yaml.safe_load(f)

# Create the client
client = TelegramClient(config["session_name"], config["api_id"], config["api_hash"])

# Connect client
client.start()
print('[Telethon] Client is listening...')

# Create a translator instance
translator = Translator()

# Get input and output entities for video listener
input_channels_entities = []
output_channel_entities = []

for d in client.iter_dialogs():
    if d.name in config["input_channel_names"] or d.entity.id in config["input_channel_ids"]:
        input_channels_entities.append(InputChannel(d.entity.id, d.entity.access_hash))
    if d.name in config["output_channel_names"] or d.entity.id in config["output_channel_ids"]:
        output_channel_entities.append(InputChannel(d.entity.id, d.entity.access_hash))
        
if not output_channel_entities:
    logger.error(f"Could not find any output channels in the user's dialogs")
    # sys.exit(1)

if not input_channels_entities:
    logger.error(f"Could not find any input channels in the user's dialogs")
    # sys.exit(1)

num_output_channels = len(output_channel_entities)
logging.info(f"[Telethon] Listening to {num_output_channels} {'channel' if num_output_channels == 1 else 'channels'}. Forwarding messages to \"{config['output_channel_names'][0]}\"...")

# Listen for new messages
@client.on(events.NewMessage)
async def handler(e):
    # Translate with Google Translator (source language is auto-detected; output language is English)
    content = translator.translate(e.message.message)

    if content.text:
        text = content.text
        chat = await e.get_chat()
        chat_name = get_chat_name(chat)

        if chat.username:
            link = f't.me/{chat.username}'
        else:
            link = f't.me/c/{chat.id}'

        # Translator mistranslates 'Тривога!' as 'Anxiety' (in this context); change to 'Alert!'
        text = text.replace('Anxiety!', 'Alert!')
        
        message_id = e.id
        flag = get_flag(content.src)
        border = '~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~'
        # message = f'📣\n\n{border}\n"{flag}" [{chat_name}]({link})\n{border}\n\n{text}\n\n[👁‍🗨]({link}/{message_id})'
        message = f'<p>📣"\n\n"</p><br><br><p>{border}</p><br><p>"{flag}" <a href="{link}">{chat_name}</a></p><br><p>{border}</p><br><br><p>{text}</p><br><br><a href="{link}/{message_id}">👁‍🗨</a>'

        if chat.username not in ['shadedPineapple', 'ryan_test_channel', 'ryan_v404', 'UkrRusWarNews', 'telehunt_video', 'cyberbenb', 'Telegram']:
            try:
                await client.send_message('https://t.me/UkrRusWarNews', message, link_preview=False, parse_mode='html')
            except:
                print('[Telethon] Error while sending message!')

# Listen for new video messages
@client.on(events.NewMessage(chats=input_channels_entities, func=lambda e: hasattr(e.media, 'document')))
async def handler(e):
    video = e.message.media.document
    if hasattr(video, 'mime_type') and bool(re.search('video', video.mime_type)):
        content = translator.translate(e.message.message)

        if content.text:
            text = content.text
            chat = await e.get_chat()

            if chat.username:
                link = f't.me/{chat.username}'
            else:
                link = f't.me/c/{chat.id}'
            
            message_id = e.id
            border = '~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~ ~'
            message = f'{link}/{message_id} ↩\n\n{border}\n{chat.title}\n{border}\n\n[ORIGINAL MESSAGE]\n{e.message.message}\n\n[TRANSLATED MESSAGE]\n{text}'
            e.message.message = message
            
            if chat.username not in ['shadedPineapple', 'ryan_test_channel', 'ryan_v404', 'UkrRusWarNews', 'telehunt_video', 'cyberbenb', 'Telegram']:
                try:
                    await client.send_message(output_channel_entities[0], e.message)
                except:
                    print('[Telethon] Error while forwarding video message!')

# Run client until a keyboard interrupt (ctrl+C)
client.run_until_disconnected()
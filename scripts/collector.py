import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetHistoryRequest

logger = logging.getLogger(__name__)

async def collect_mentions(config, since=None):
    tg = config["telegram"]
    mon = config["monitor"]
    if since is None:
        since = datetime.now(tz=timezone.utc) - timedelta(hours=mon["lookback_hours"])
    keywords = [kw.lower() for kw in mon["keywords"]]
    client = TelegramClient(tg["session_name"], int(tg["api_id"]), tg["api_hash"])
    mentions = []
    async with client:
        for chat_username in mon["chats"]:
            logger.info("Scanning chat: %s", chat_username)
            try:
                entity = await client.get_entity(chat_username)
                offset_id = 0
                total_scanned = 0
                stop = False
                while not stop:
                    messages = await client(GetHistoryRequest(
                        peer=entity, limit=100, offset_date=None,
                        offset_id=offset_id, max_id=0, min_id=0,
                        add_offset=0, hash=0,
                    ))
                    if not messages.messages:
                        break
                    for msg in messages.messages:
                        if not msg.message:
                            continue
                        msg_date = msg.date.replace(tzinfo=timezone.utc)
                        if msg_date < since:
                            stop = True
                            break
                        total_scanned += 1
                        if any(kw in msg.message.lower() for kw in keywords):
                            mentions.append({
                                "chat": chat_username,
                                "message_id": msg.id,
                                "date": msg.date,
                                "text": msg.message,
                            })
                    offset_id = messages.messages[-1].id
                    await asyncio.sleep(0.5)
                logger.info("Chat %s: scanned %d messages", chat_username, total_scanned)
            except Exception as exc:
                logger.warning("Error scanning %s: %s", chat_username, exc)
    logger.info("Collected %d mentions", len(mentions))
    return mentions

async def start_live_listener(config, on_mention):
    tg = config["telegram"]
    mon = config["monitor"]
    keywords = [kw.lower() for kw in mon["keywords"]]
    client = TelegramClient(tg["session_name"], int(tg["api_id"]), tg["api_hash"])
    @client.on(events.NewMessage(chats=mon["chats"]))
    async def handler(event):
        text = event.message.message or ""
        if any(kw in text.lower() for kw in keywords):
            await on_mention(event.chat.username, text)
    await client.start()
    logger.info("Live listener started")
    await client.run_until_disconnected()

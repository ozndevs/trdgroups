from pyrogram import Client, Filters
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import add_point, get_trending, valid_point
from utils import clear_db, generate_msg, migrate_chat
from config import TOKEN, API_ID, API_HASH, TRD_CHAT


c = Client("bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)


@c.on_message(Filters.command("start") & Filters.private)
async def start(client, message):
    await message.reply_text(f"Olá **{message.from_user.first_name}** 🥳 vamos ver se seu grupo está em nosso"
                             "ranking semanal de interação entre os membros?\n\n"

                             "Leia as regras no botão (ler as regras)")


@c.on_message(Filters.command("trending") & Filters.private)
async def trending(client, message):
    trd = generate_msg(get_trending())
    await message.reply_text(trd)


@c.on_message(Filters.group, group=-1)
async def process_msg(client, message):
    if message.migrate_from_chat_id:
        migrate_chat(message.migrate_from_chat_id, message.chat.id)
    elif not message.service and valid_point(message.chat.id, message.from_user.id, message.date):
        if message.reply_to_message:
            count = 2
        else:
            count = 1
        add_point(message.chat.id, message.chat.title, count)


async def daily_trendings():
    msg = generate_msg(get_trending())
    await c.send_message(TRD_CHAT, msg)

async def weekly_trendings():
    msg = generate_msg(get_trending())
    clear_db()
    await c.send_message(TRD_CHAT, msg)


scheduler = AsyncIOScheduler()

scheduler.configure(timezone="America/Sao_Paulo")

scheduler.add_job(daily_trendings, "cron", day_of_week="tue-sun")
scheduler.add_job(weekly_trendings, "cron", day_of_week="mon")

scheduler.start()
c.run()

from pyrogram import Client, Filters, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import add_point, get_trending, valid_point
from utils import clear_db, generate_msg, migrate_chat
from config import TOKEN, API_ID, API_HASH, TRD_CHAT, VERSION


c = Client("bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)


@c.on_message(Filters.command("start") & Filters.private)
@c.on_callback_query(Filters.callback_data("start_back"))
async def start(client, message):
    if isinstance(message, CallbackQuery):
        send = message.message.edit_text
    else:
        send = message.reply_text
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📖 Info", callback_data="infos")]+
        [InlineKeyboardButton("📮 Regras", callback_data="regras")],
        [InlineKeyboardButton("Adicionar em um grupo", url="https://t.me/trdgroupsbot?startgroup=new")]
    ])

    await send(f"Olá **{message.from_user.first_name}** 🥳 vamos ver se seu grupo está em nosso "
               "ranking semanal de interação entre os membros?\n\n"

               "Leia as regras no botão (ler as regras)",
                reply_markup=kb)


@c.on_message(Filters.command("trending") & Filters.private)
async def trending(client, message):
    trd = get_trending()
    if trd:
        msg = generate_msg(trd)
    else:
        msg = """**Ooops ⚠️! Fiz uma pesquisa aqui e não há dados de grupos em meu sistema, tente novamente mais tarde ou outro dia.

😃👋 Obrigado (a) pela compreensão**"""
    await message.reply_text(msg)


@c.on_callback_query(Filters.callback_data("regras"))
async def regras(client, message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("« Voltar", callback_data="start_back")]
    ])

    await message.message.edit_text("""📮 Regras

`⭕️ Proibido grupos que tenham spam, pornô ou violência
⭕️ Proibido adicionar o bot em grupos de vendas ou coisas ilegais`

Caso tenha um grupo desses em nosso sistema, ele poderá ser excluído do mesmo sem aviso prévio.

**📌 OBS:** __Novas regras poderão ser adicionadas conforme o tempo for passando :)__

**Obrigado por ser um colaborador do nosso bot 🥰**""", reply_markup=kb)


@c.on_callback_query(Filters.callback_data("infos"))
async def infos(client, message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("« Voltar", callback_data="start_back")]
    ])

    await message.message.edit_text(f"""Nome: Trending Groups
User: @trdgroupsbot
Versão: {VERSION}
Devs: AMANOTEAM
Org: OZN

OBS: Caso você precice de ajuda para usar o bot, sinta-se à vontade para nos contatar pelo @SuporteBuilderBot.""",
                                    reply_markup=kb)


@c.on_message(Filters.group | Filters.migrate_from_chat_id, group=-1)
async def process_msg(client, message):
    if message.migrate_from_chat_id:
        migrate_chat(message.migrate_from_chat_id, message.chat.id)
    elif valid_point(message.chat.id, message.from_user.id, message.date):
        if message.reply_to_message and not message.reply_to_message.from_user.is_bot and message.from_user.id != message.reply_to_message.from_user.id:
            count = 2
        else:
            count = 1
        add_point(message.chat.id, message.chat.title, count)


async def send_trending_msg(chat):
    # [0] = title, [1] = id, [2] = points
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("👀 Ver o ranking", url="https://t.me/trdgroups")]
    ])
    try:
        await c.send_message(chat[1], f"""**Wooow 😯!** {chat[0]} Acabei de postar o ranking no meu canal, bora ver se esse grupo está nós tops?

Aperte no botão abaixo (👀 Ver o ranking)""", reply_markup=kb)
    except:
        return False
    else:
        return True


async def daily_trendings():
    trd = get_trending()
    msg = generate_msg(trd)
    await c.send_message(TRD_CHAT, msg)
    for chat in trd:
        await send_trending_msg(chat)

async def weekly_trendings():
    trd = get_trending()
    msg = generate_msg(trd)
    clear_db()
    await c.send_message(TRD_CHAT, msg)
    for chat in trd:
        await send_trending_msg(chat)


scheduler = AsyncIOScheduler()

scheduler.configure(timezone="America/Sao_Paulo")

scheduler.add_job(daily_trendings, "cron", day_of_week="tue-sun")
scheduler.add_job(weekly_trendings, "cron", day_of_week="mon")

scheduler.start()
c.run()

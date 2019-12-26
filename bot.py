from pyrogram import Client, Filters, InlineKeyboardMarkup, InlineKeyboardButton
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import add_point, get_trending, valid_point
from utils import clear_db, generate_msg, migrate_chat
from config import TOKEN, API_ID, API_HASH, TRD_CHAT, VERSION


c = Client("bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)


@c.on_message(Filters.command("start") & Filters.private)
async def start(client, message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📖 Info", callback_data="infos")]+
        [InlineKeyboardButton("📮 Regras", callback_data="regras")],
        [InlineKeyboardButton("Adicionar em um grupo", url="https://t.me/trdgroupsbot?startgroup=new")]
    ])
    await message.reply_text(f"Olá **{message.from_user.first_name}** 🥳 vamos ver se seu grupo está em nosso "
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
    await message.message.edit_text("""📮 Regras

`⭕️ Proibido Grupos que tenham spam, porno ou violência ( caso tenha um grupo desse em nosso sistema, ele poderá ser excluído sem aviso prévio)

⭕️ Proibido colocar em grupos de vendas e coisas ilegais na internet

⭕️ Por favor evite chamar os administradores do bot no privado sem motivo! Sabendo que o bot já tem o` @SuporteBuilderBot `ele fica 24/7 aberto`

**📌 OBS:** __as regras serão adicionadas conforme o tempo for passando :)__

**Obrigado por ser um colaborador de nosso bot 🥰**""")


@c.on_callback_query(Filters.callback_data("infos"))
async def infos(client, message):
    await message.message.edit_text(f"""Nome: Trending Groups
User: @trdgroupsbot
Versão: {VERSION}
Devs: AMANOTEAM
Org: OZN""")


@c.on_message(Filters.group, group=-1)
async def process_msg(client, message):
    if message.migrate_from_chat_id:
        migrate_chat(message.migrate_from_chat_id, message.chat.id)
    elif not message.service and valid_point(message.chat.id, message.from_user.id, message.date):
        if message.reply_to_message and not message.reply_to_message.from_user.is_bot and message.from_user.id != message.reply_to_message.from_user.id:
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

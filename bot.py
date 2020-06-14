from distutils.util import strtobool

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pyrogram import Client, Filters, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import TOKEN, API_ID, API_HASH, TRD_CHAT, VERSION, SUDOERS
from db import add_point, get_trending, valid_point, get_configs, change_configs
from utils import clear_db, generate_msg, migrate_chat, callback_starts, get_switch

c = Client("bot", bot_token=TOKEN, api_id=API_ID, api_hash=API_HASH)


async def is_admin(chat_id, user_id):
    res = await c.get_chat_member(chat_id, user_id)

    if res.status == "administrator" or res.status == "creator":
        return True
    else:
        return False


@c.on_message(Filters.command("start") & Filters.private)
@c.on_callback_query(Filters.callback_data("start_back"))
async def start(client, message):
    if isinstance(message, CallbackQuery):
        send = message.message.edit_text
    else:
        send = message.reply_text
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("📖 Info", callback_data="infos")] +
        [InlineKeyboardButton("📮 Regras", callback_data="rules")] +
        [InlineKeyboardButton("📕 Ajuda", callback_data="help")],
        [InlineKeyboardButton("Adicionar em um grupo", url="https://t.me/trdgroupsbot?startgroup=new")] +
        [InlineKeyboardButton("🌟 Avaliar", callback_data="rate_bot")]
    ])

    await send(f"Olá **{message.from_user.first_name}** 🥳 vamos ver se seu grupo estará em nosso "
                "ranking semanal de interação entre os membros?\n\n"

                "Leia as regras no botão abaixo (📮 Regras)",
               reply_markup=kb)


@c.on_callback_query(Filters.callback_data("rate_bot"))
async def rate_bot(client, message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🙂 Bom", callback_data="rate_callback good")] +
        [InlineKeyboardButton("🤩 Ótimo", callback_data="rate_callback awesome")] +
        [InlineKeyboardButton("😕 Razoável", callback_data="rate_callback reasonable")] +
        [InlineKeyboardButton("😖 Péssimo", callback_data="rate_callback terrible")],
        [InlineKeyboardButton("« Voltar", callback_data="start_back")]
    ])

    await message.message.edit_text(f"Olá **{message.from_user.first_name}** 👋😁! Nós da equipe do **Trending Groups** queremos saber o quanto você está satisfeito com o nosso bot 🤔\n\n"

                "Avalie ele clicando no botão abaixo e depois faça uma resenha sobre o nível de satisfação que você teve com as funções do **Trending Groups** 🙂",
               reply_markup=kb)


@c.on_message(Filters.command("trending") & Filters.private)
@c.on_callback_query(Filters.callback_data("update_trd"))
async def trending(client, message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🔁 Atualizar", callback_data="update_trd")]
    ])

    trd = get_trending()
    if trd:
        msg = generate_msg(trd)
    else:
        msg = """**Ooops ⚠️! Fiz uma pesquisa aqui e não há dados de grupos em meu sistema, tente novamente mais tarde ou outro dia.

😃👋 Obrigado (a) pela compreensão**"""

    if isinstance(message, CallbackQuery):
        if message.message.text.markdown == msg:
            return await message.answer("Os trendings já estão atualizados.")
        send = message.message.edit_text
    else:
        send = message.reply_text

    await send(msg, reply_markup=kb, disable_web_page_preview=True)


@c.on_message(Filters.command("banchat", "!") & Filters.user(SUDOERS))
async def banchat(client, message):
    m = await message.reply_text(f"Banindo o chat {message.command[1]}...")
    try:
        chat = int(message.command[1])
    except ValueError:
        chat = message.command[1]

    try:
        chat = await client.get_chat(chat)
    except Exception as e:
        await m.edit_text(str(e))
    else:
        change_configs(chat.id, "is_banned", True)
        await m.edit_text(
            f"Chat {chat.title} (`{chat.id}`) banido com sucesso. Seus pontos não irão ser contados mais e não serão exibidos nos trendings.")


@c.on_message(Filters.command("unbanchat", "!") & Filters.user(SUDOERS))
async def banchat(client, message):
    m = await message.reply_text(f"Desbanindo o chat {message.command[1]}...")
    try:
        chat = int(message.command[1])
    except ValueError:
        chat = message.command[1]

    try:
        chat = await client.get_chat(chat)
    except Exception as e:
        await m.edit_text(str(e))
    else:
        change_configs(chat.id, "is_banned", False)
        await m.edit_text(f"Chat {chat.title} (`{chat.id}`) desbanido com sucesso.")


@c.on_message(Filters.command("settings") & Filters.group)
async def settings(client, message):
    configs = get_configs(message.chat.id)
    if await is_admin(message.chat.id, message.from_user.id):
        try:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("🛎 Notificar", callback_data="notify_help")] +
                [InlineKeyboardButton(get_switch(configs["notifications_optin"]),
                                      callback_data=f"notify_status {message.chat.id} {not configs['notifications_optin']}")],
                [InlineKeyboardButton("🔗 Linkar grupo", callback_data="linkchat_help")] +
                [InlineKeyboardButton(get_switch(configs["link_optin"]),
                                      callback_data=f"linkchat_status {message.chat.id} {not configs['link_optin']}")]
            ])
            await client.send_message(message.from_user.id, f"Painel de controle para o grupo {configs['title']}",
                                      reply_markup=kb)
        except:
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton("🤖 Iniciar conversa", url="https://t.me/trdgroupsbot")]
            ])
            await message.reply_text("Você deve primeiro iniciar uma conversa privada comigo.")
            raise
        else:
            await message.reply_text("Eu enviei uma mensagem privada com as configs deste grupo.")


@c.on_message(Filters.command(["rank", "stats"]) & Filters.group)
async def rank(client, message):
    trd = get_trending(999999999)
    for pos, chat in enumerate(trd):
        if chat[1] == message.chat.id:
            msg = f"""**📊 Rank Stats

👥 Grupo:** `{message.chat.title}`
**🏆 Posição:** `{pos + 1}`
**👓 Pontuação:** `{chat[2]}`

**📌 Essas são as informações da rank do grupo de acordo com o meu banco de dados.**"""
            return await message.reply_text(msg)
    else:
        return await message.reply_text(f"Este grupo ainda não tem dados de pontuação aqui.")


@c.on_callback_query(Filters.callback_data("notify_help"))
async def notify_help(client, message):
    await message.answer(
        "🛎 Notificar\n\nEsta configuração define se o bot deve enviar uma mensagem no grupo caso o mesmo estiver no top 10 dos trendings.",
        show_alert=True)


@c.on_callback_query(Filters.callback_data("linkchat_help"))
async def linkchat_help(client, message):
    await message.answer(
        "🔗 Linkar grupo\n\nEsta configuração define se o bot deve incluir um link (público) para o grupo caso ele aparecer nos trendings.",
        show_alert=True)


@c.on_callback_query(callback_starts("notify_status"))
async def notify_status(client, message):
    _, chat, new_status = message.data.split()
    chat = int(chat)
    new_status = strtobool(new_status)

    change_configs(chat, "notifications_optin", new_status)
    configs = get_configs(chat)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🛎 Notificar", callback_data="notify_help")] +
        [InlineKeyboardButton(get_switch(configs["notifications_optin"]),
                              callback_data=f"notify_status {chat} {not configs['notifications_optin']}")],
        [InlineKeyboardButton("🔗 Linkar grupo", callback_data="linkchat_help")] +
        [InlineKeyboardButton(get_switch(configs["link_optin"]),
                              callback_data=f"linkchat_status {chat} {not configs['link_optin']}")]
    ])

    await message.message.edit_text("Painel de controle para o grupo " + configs["title"], reply_markup=kb)


@c.on_callback_query(callback_starts("linkchat_status"))
async def linkchat_status(client, message):
    _, chat, new_status = message.data.split()
    chat = int(chat)
    new_status = strtobool(new_status)

    change_configs(chat, "link_optin", new_status)
    configs = get_configs(chat)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("🛎 Notificar", callback_data="notify_help")] +
        [InlineKeyboardButton(get_switch(configs["notifications_optin"]),
                              callback_data=f"notify_status {chat} {not configs['notifications_optin']}")],
        [InlineKeyboardButton("🔗 Linkar grupo", callback_data="linkchat_help")] +
        [InlineKeyboardButton(get_switch(configs["link_optin"]),
                              callback_data=f"linkchat_status {chat} {not configs['link_optin']}")]
    ])

    await message.message.edit_text("Painel de controle para o grupo " + configs["title"], reply_markup=kb)


@c.on_callback_query(Filters.callback_data("rules"))
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
Org: OZN""",
                                    reply_markup=kb)


@c.on_callback_query(Filters.callback_data("help"))
async def help(client, message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("« Voltar", callback_data="start_back")]
    ])

    text = """📕 Ajuda

Comandos:
`/stats` - Envia as estatísticas de um grupo. (Somente no grupo)
`/settings` - Envia o menu de configurações do grupo. (Somente admin)
`/trending` - Envia os top 15 chats no bot. (Somente no privado)

OBS: Caso você precise de ajuda para usar o bot, sinta-se à vontade para nos contatar pelo @trdsuportebot."""

    await message.message.edit_text(text, reply_markup=kb)


@c.on_message(Filters.group | Filters.migrate_from_chat_id, group=-1)
async def process_msg(client, message):
    if message.migrate_from_chat_id:
        migrate_chat(message.migrate_from_chat_id, message.chat.id)
    elif valid_point(message.chat.id, message.from_user.id, message.date):
        if message.reply_to_message and not message.reply_to_message.from_user.is_bot and message.from_user.id != message.reply_to_message.from_user.id:
            count = 2
        else:
            count = 1
        add_point(message.chat.id, message.chat.title, message.chat.username, count)


async def send_trending_msg(chat):
    # [0] = title, [1] = id, [2] = points, [3] = notifications_optin, [4] = link_optin, [5] = chat_link
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("Ver o ranking", url="https://t.me/trdgroups")]
    ])
    if chat[3]:
        try:
            await c.send_message(chat[1],
                                 f"""Olá **{chat[0]}**, acabei de postar o ranking no meu canal. Vamos ver em qual posição esse grupo ficou? 🤔

Se você quiser ver o ranking, clique no botão abaixo:""", reply_markup=kb)
        except:
            return False
        else:
            return True


async def daily_trendings():
    trd = get_trending()
    msg = generate_msg(trd)
    await c.send_message(TRD_CHAT, msg, disable_web_page_preview=True)
    for chat in trd:
        await send_trending_msg(chat)


async def weekly_trendings():
    trd = get_trending()
    msg = generate_msg(trd)
    clear_db()
    await c.send_message(TRD_CHAT, msg, disable_web_page_preview=True)
    for chat in trd:
        await send_trending_msg(chat)


scheduler = AsyncIOScheduler()

scheduler.configure(timezone="America/Sao_Paulo")

scheduler.add_job(daily_trendings, "cron", day_of_week="tue-sun")
scheduler.add_job(weekly_trendings, "cron", day_of_week="mon")

scheduler.start()
c.run()

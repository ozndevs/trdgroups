from db import cur, con
from pyrogram import filters


def generate_msg(sql_chats):
    # [0] = title, [1] = id, [2] = points, [3] = notifications_optin, [4] = link_optin, [5] = chat_link
    msg = ["🏆 Trending **Groups**\n"]
    for position, chat in enumerate(sql_chats):
        if position == 0:
            prefix = "🥇"
        elif position == 1:
            prefix = "🥈"
        elif position == 2:
            prefix = "🥉"
        else:
            prefix = "🌟"
        if chat[4] and chat[5]:
            msg.append(f"{prefix}: [{chat[0]}](https://t.me/{chat[5]}) ({chat[2]} pontos)")
        else:
            msg.append(f"{prefix}: {chat[0]} ({chat[2]} pontos)")
    return "\n".join(msg)


def clear_db():
    cur.execute("UPDATE trd_chats SET chat_points = ?", (0,))
    con.commit()


def migrate_chat(old_chat, new_chat):
    cur.execute("UPDATE trd_chats SET chat_id = ? WHERE chat_id = ?", (new_chat, old_chat))
    con.commit()


def callback_starts(data: str or bytes):
    return filters.create(lambda flt, cb: cb.data.split()[0] == flt.data, "CallbackStartsFilter", data=data)


def get_switch(status: bool or int):
    return "✅ ON" if status else "☑️ OFF"
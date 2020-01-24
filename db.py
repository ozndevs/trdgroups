import sqlite3

con = sqlite3.connect("trdgroups.db")
cur = con.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS trd_chats (chat_id INTEGER,
                                                     chat_title,
                                                     chat_points INTEGER,
                                                     chat_lang,
                                                     is_banned INTEGER,
                                                     notifications_optin INTEGER,
                                                     link_optin INTEGER,
                                                     chat_link)''')

cur.execute('''CREATE TABLE IF NOT EXISTS flood_ctl (chat_id INTEGER,
                                                     user_id INTEGER,
                                                     last_timestamp INTEGER)''')

con.commit()


def chat_exists(chat_id):
    cur.execute("SELECT chat_id from trd_chats WHERE chat_id = ?", (chat_id,))
    res = cur.fetchone()
    if res:
        return True
    else:
        return False


def valid_point(chat_id, user_id, timestamp):
    usr = cur.execute("SELECT last_timestamp from flood_ctl WHERE chat_id = ? AND user_id = ?", (chat_id, user_id))
    res = cur.fetchone()
    if res:
        cur.execute("UPDATE flood_ctl SET last_timestamp = ? WHERE chat_id = ? AND user_id = ?",
                    (timestamp, chat_id, user_id))
        return res[0] <= timestamp - 2
    else:
        cur.execute("INSERT INTO flood_ctl (chat_id, user_id, last_timestamp) VALUES (?,?,?)",
                    (chat_id, user_id, timestamp))
        con.commit()
        return True


def add_point(chat_id, chat_title, chat_link=None, count=1):
    if chat_exists(chat_id):
        cur.execute(
            "UPDATE trd_chats SET chat_title = ?, chat_link = ?, chat_points = chat_points + ? WHERE chat_id = ? AND is_banned = ?",
            (chat_title, chat_link, count, chat_id, 0))
        con.commit()
    else:
        cur.execute(
            "INSERT INTO trd_chats (chat_id, chat_title, chat_link, chat_points, notifications_optin, is_banned) VALUES (?,?,?,?,?,?)",
            (chat_id, chat_title, chat_link, count, 1, 0))
        con.commit()


def get_trending(max_chats=15):
    cur.execute(
        "SELECT chat_title, chat_id, chat_points, notifications_optin, link_optin, chat_link FROM trd_chats WHERE chat_points > ? and is_banned = 0 ORDER BY chat_points DESC LIMIT ?",
        (0, max_chats))
    return cur.fetchall()


def get_configs(chat_id: int):
    cur.execute(
        "SELECT chat_title, chat_points, link_optin, chat_link, notifications_optin FROM trd_chats WHERE chat_id = ?",
        (chat_id,))
    res = cur.fetchone()
    return dict(title=res[0], points=res[1], link_optin=res[2], link=res[3], notifications_optin=res[4])


def change_configs(chat_id: int, config_name: str, value: str or int):
    cur.execute(f"UPDATE trd_chats SET {config_name} = ? WHERE chat_id = ?", (value, chat_id))
    con.commit()

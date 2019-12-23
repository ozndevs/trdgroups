import sqlite3


con = sqlite3.connect("trdgroups.db")
cur = con.cursor()

cur.execute('''CREATE TABLE IF NOT EXISTS trd_chats (chat_id INTEGER,
                                                     chat_title,
                                                     chat_points INTEGER,
                                                     chat_lang)''')

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
        cur.execute("UPDATE flood_ctl SET last_timestamp = ? WHERE chat_id = ? AND user_id = ?", (timestamp, chat_id, user_id))
        return res[0] <= timestamp-2
    else:
        cur.execute("INSERT INTO flood_ctl (chat_id, user_id, last_timestamp) VALUES (?,?,?)", (chat_id, user_id, timestamp))
        con.commit()
        return True


def add_point(chat_id, chat_title, count=1):
    if chat_exists(chat_id):
        cur.execute("UPDATE trd_chats SET chat_title = ?, chat_points = chat_points + ? WHERE chat_id = ?", (chat_title, count, chat_id))
        con.commit()
    else:
        cur.execute("INSERT INTO trd_chats (chat_id, chat_title, chat_points) VALUES (?,?,?)", (chat_id, chat_title, count))
        con.commit()


def get_trending(max_chats=10):
    cur.execute("SELECT chat_title, chat_id, chat_points FROM trd_chats ORDER BY chat_points DESC LIMIT ?", (max_chats,))
    return cur.fetchall()

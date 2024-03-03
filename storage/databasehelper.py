import base64
import pickle
import sqlite3

import discord

from storage.classes import *


def save():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()

    c.execute('DELETE FROM gpt_users')
    c.execute('DELETE FROM requests')

    for gpt_user in _gpt_users:
        obj_base64 = base64.b64encode(pickle.dumps(gpt_user)).decode('utf-8')
        c.execute('INSERT INTO gpt_users (id, object) VALUES (?,?)', (gpt_user.id, obj_base64))

    # Save requests
    for user_id, requests in _requests_map.items():
        obj_base64 = base64.b64encode(pickle.dumps(requests)).decode('utf-8')
        c.execute('INSERT INTO requests (id, object) VALUES (?,?)', (user_id, obj_base64))

    conn.commit()
    conn.close()


def test():
    print("test")


_gpt_users: QueueableList[GPTUser] = QueueableList(callback=save)
_requests_map: QueueableDict[int, List[GPTRequest]] = QueueableDict(callback=save)


def setup_database():
    conn = sqlite3.connect('database.db')
    setup_gpt_users(conn)
    setup_requests(conn)
    load_gpt_users(conn)
    load_requests(conn)
    conn.close()


def setup_gpt_users(conn: sqlite3.Connection):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS gpt_users
                 (id INTEGER PRIMARY KEY,  object TEXT)''')
    conn.commit()


def setup_requests(conn: sqlite3.Connection):
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS requests
                 (id INTEGER PRIMARY KEY,  object TEXT)''')
    conn.commit()


def load_gpt_users(conn: sqlite3.Connection) -> None:
    global _gpt_users
    c = conn.cursor()
    c.execute('SELECT * FROM gpt_users')
    rows = c.fetchall()
    for row in rows:
        obj_base64 = row[1]
        obj = pickle.loads(base64.b64decode(obj_base64))
        _gpt_users.append(obj)


def load_requests(conn: sqlite3.Connection) -> None:
    global _requests_map
    c = conn.cursor()
    c.execute('SELECT * FROM requests')
    rows = c.fetchall()
    for row in rows:
        obj_base64 = row[1]
        obj = pickle.loads(base64.b64decode(obj_base64))
        _requests_map[row[0]] = obj


def add_user(user: discord.User, channel: discord.TextChannel):
    gpt_user = GPTUser(user.id, 0, False, GPTChannel(
        id=channel.id
    ))
    _gpt_users.append(gpt_user)


def add_request(user: GPTUser, request: GPTRequest):
    if user.id in _requests_map:
        _requests_map[user.id].append(request)
        _requests_map[user.id] = _requests_map[user.id]
    else:
        _requests_map[user.id] = [request]


def remove_user(user: GPTUser):
    _gpt_users.remove(user)


def get_gpt_users() -> List[GPTUser]:
    return _gpt_users


def get_requests() -> dict[int, List[GPTRequest]]:
    return _requests_map

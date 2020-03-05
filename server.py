import asyncio
import sys
import sqlite3
import datetime

def add_new_user(username, password):
    query_user = "Insert into user values(?, ?, datetime('now','+3 HOURS'))"
    cursor.execute(query_user, (username, password))

def add_message(username, reciever, message_text, date):
    query_message = "Insert into message values(?, ?, ?, ?)"
    print(date)
    cursor.execute(query_message, (username, reciever, message_text, date))

def check_password(username, password):
    query_get_password = "Select password from user where username = ?"
    cursor.execute(query_get_password, (username,))
    if cursor.fetchone()[0] == password:
        return True
    else:
        return False

def get_message_log(username, writer):
    query_get_last_online = "Select last_online from user where username = ?"
    cursor.execute(query_get_last_online, (username, ))
    last_online = cursor.fetchall()[0][0]
    print(last_online)
    query_get_message_log = "Select username, reciever, date, message_text from message where date > ?"
    cursor.execute(query_get_message_log, (last_online, ))
    messages = cursor.fetchall()
    if messages != []:
        for message in messages:
            if message[1] == "broadcast":
                writer.write(f"[{message[2]}] {message[0]}: {message[3]}\n".encode())
            elif message[1] == username:
                writer.write(f"[{message[2]}] {message[0]}(to you): {message[3]}\n".encode())
    writer.write('1\n'.encode())

def update_last_online(user):
    query_update_last_online = "Update user set last_online = datetime('now', '+3 HOURS') where username = ?"
    cursor.execute(query_update_last_online, (user.username, ))

def get_user_log():
    query_get_user_log = "Select username from user"
    cursor.execute(query_get_user_log)
    user_log = []
    while True:
        user = cursor.fetchone()
        if user == None:
            break
        user_log.append(user[0])
    return user_log



class User:

    def __init__(self, writer, username):
        self.writer = writer
        self.username = username

class Users:
    
    def __init__(self):
        self.user_list = []
    
    def add(self, user):
        self.user_list.append(user)

    async def forward(self, sender, reciever_username, message, date):
        is_message = False
        for u in get_user_log():
            if u.username == reciever_username:
                u.writer.write(f"[{date}]{sender.username!s}(to you): {message!s}".encode())
                await u.writer.drain()
                add_message(sender.username, reciever_username, message, date)
                is_message = True
        if is_message == False:
            sender.writer.write('No user found'.encode())     
            await sender.writer.drain() 

    
    async def broadcast(self, sender, message, date):
        for u in self.user_list:
            if u.username != sender.username:
                u.writer.write(f"[{date}]{sender.username!s}: {message!s}".encode())
                await u.writer.drain()
                add_message(sender.username, 'broadcast', message, date)

    async def login(self, reader, writer):
        while True:
            username = (await reader.read(20)).decode()
            if reader.at_eof():
                return False
            if username not in get_user_log(): # Новый пользователь
                writer.write('1'.encode()) # Код для клиента о том, что создание нового пользователя прошло успешно
                add_new_user(username, (await reader.read(255)).decode()) # Ожидаем ввод пароля
                if reader.at_eof():
                    return False     
                return username
            else: # Существующий пользователь
                print('here')
                writer.write('2'.encode()) # Код для клиента о том, что пользователь уже существует, в клиенте запрашивается пароль
                while True:
                    password = (await reader.read(255)).decode()
                    if reader.at_eof():
                        return False
                    if check_password(username, password):
                        writer.write('1'.encode()) # Пароль верный
                        return username
                    writer.write('0'.encode()) # Пароль неверный


    def end_user_session(self, user):
        update_last_online(user)
        self.user_list.remove(user)
        user.writer.close()


users = Users()

async def handle(reader, writer):
    password = await users.login(reader, writer)
    if password:
        user = User(writer, password)
    else:
        return
    users.add(user)
    get_message_log(user.username, writer)
    message = f"{user.username!s} is connected !!!!"
    await users.broadcast(user, message, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    while True:
        data = (await reader.readline()).decode()
        if reader.at_eof():
            users.end_user_session(user)
            return
        date = data.split()[0] + ' ' + data.split()[1]
        message = data.split(maxsplit = 2)[2]
        if message[:2] == '/w':
            reciever_username = message.split()[1]
            message_text = message.split(maxsplit = 2)[2]
            print(reciever_username + ' //// ' + message_text)
            await users.forward(user, reciever_username, message_text, date)
        else:
            await users.broadcast(user, message, date)

async def main():
    if len(sys.argv) == 3:
        ip = sys.argv[1]
        port = sys.argv[2]
    else:
        print('Correct formatting: script name, IP address, port')
        return
    server = await asyncio.start_server(handle, ip, port)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr!s}')
    async with server:
        await server.serve_forever()

cnx = sqlite3.connect(':memory:')
cursor = cnx.cursor()
cursor.execute("PRAGMA foreign_keys = ON;")
cursor.execute('''CREATE TABLE user (
                username text PRIMARY KEY,
                password text,
                last_online text)''')
cursor.execute('''CREATE TABLE message
                (username text,
                reciever text,
                message_text text,
                date text,
                FOREIGN KEY(username) REFERENCES user (username))''')
asyncio.run(main())
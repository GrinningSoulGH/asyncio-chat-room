import asyncio
from chat_utils.chatdatabase import ChatDatabase

class User:

    def __init__(self, writer, username):
        self.writer = writer
        self.username = username

class ChatRoom:
    
    def __init__(self):
        self.user_list = []
        self.db = ChatDatabase()

    async def start_database_server(self, filename = False):
        await self.db.create_connection(filename)
        await self.db.cursor.execute("PRAGMA foreign_keys = ON;")
        await self.db.cursor.execute('''CREATE TABLE user (
                        username text PRIMARY KEY,
                        password text,
                        last_online text)''')
        await self.db.cursor.execute('''CREATE TABLE message
                        (username text,
                        reciever text,
                        message_text text,
                        date text,
                        FOREIGN KEY(username) REFERENCES user (username))''')
        

    def add(self, user):
        self.user_list.append(user)

    async def forward(self, sender, reciever_username, message, date):
        is_message = False
        if reciever_username in await self.db.get_user_log():
            await self.db.add_message(sender.username, reciever_username, message, date)
            is_message = True
        for u in self.user_list:
            if u.username == reciever_username:
                u.writer.write(f"[{date}]{sender.username!s}(to you): {message!s}".encode())
                await u.writer.drain()
        if is_message == False:
            sender.writer.write('No user found\n'.encode())     
            await sender.writer.drain() 

    
    async def broadcast(self, sender, message, date):
        await self.db.add_message(sender.username, 'broadcast', message, date)
        for u in self.user_list:
            if u.username != sender.username:
                u.writer.write(f"[{date}]{sender.username!s}: {message!s}".encode())
                await u.writer.drain()


    async def send_message(self, user, data):
        date = data.split()[0] + ' ' + data.split()[1]
        message = data.split(maxsplit = 2)[2]
        if message.split()[0] == '/w':
            reciever_username = message.split()[1]
            message_text = message.split(maxsplit = 2)[2]
            await self.forward(user, reciever_username, message_text, date)
        else:
            await self.broadcast(user, message, date)

    async def login(self, reader, writer):
        while True:
            username = (await reader.read(20)).decode()
            if reader.at_eof():
                return False
            if username not in await self.db.get_user_log(): # Новый пользователь
                writer.write('1'.encode()) # Код для клиента о том, что создание нового пользователя прошло успешно
                password = (await reader.read(255)).decode()
                if reader.at_eof():
                    return False  
                await self.db.add_new_user(username, password) # Ожидаем ввод пароля   
                return username
            else: # Существующий пользователь
                if username in [u.username for u in self.user_list]:
                    writer.write('2'.encode()) #Код для клиента о том, что пользователь уже онлайн
                else:
                    writer.write('3'.encode()) # Код для клиента о том, что пользователь уже существует, в клиенте запрашивается пароль
                    while True:
                        password = (await reader.read(255)).decode()
                        if reader.at_eof():
                            return False
                        if await self.db.check_password(username, password):
                            writer.write('1'.encode()) # Пароль верный
                            return username
                        writer.write('0'.encode()) # Пароль неверный


    async def end_user_session(self, user):
        await self.db.update_last_online(user)
        self.user_list.remove(user)
        user.writer.close()
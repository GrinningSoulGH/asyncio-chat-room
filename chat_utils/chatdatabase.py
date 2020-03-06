import aiosqlite
import asyncio

class ChatDatabase:
    
    def __init__(self):
        self.connection = None
        self.cursor = None

    async def create_connection(self, filename = False):
        if filename:
            self.connection = await aiosqlite.connect(f'{filename}')
        else:
            self.connection = await aiosqlite.connect(':memory:')
        self.cursor = await self.connection.cursor()
    
    async def add_new_user(self, username, password):
        query_user = "Insert into user values(?, ?, datetime('now','+3 HOURS'))"
        await self.cursor.execute(query_user, (username, password))

    async def add_message(self, username, reciever, message_text, date):
        query_message = "Insert into message values(?, ?, ?, ?)"
        await self.cursor.execute(query_message, (username, reciever, message_text, date))

    async def check_password(self, username, password):
        query_get_password = "Select password from user where username = ?"
        await self.cursor.execute(query_get_password, (username,))
        if (await self.cursor.fetchone())[0] == password:
            return True
        else:
            return False

    async def get_message_log(self, writer, username):
        query_get_last_online = "Select last_online from user where username = ?"
        await self.cursor.execute(query_get_last_online, (username, ))
        last_online = (await self.cursor.fetchall())[0][0]
        query_get_message_log = "Select username, reciever, date, message_text from message where date > ?"
        await self.cursor.execute(query_get_message_log, (last_online, ))
        messages = await self.cursor.fetchall()
        if messages != []:
            for message in messages:
                if message[1] == "broadcast":
                    writer.write(f"[{message[2]}]{message[0]}: {message[3]}".encode())
                elif message[1] == username:
                    writer.write(f"[{message[2]}]{message[0]}(to you): {message[3]}".encode())
        writer.write('1\n'.encode())

    async def update_last_online(self, user):
        query_update_last_online = "Update user set last_online = datetime('now', '+3 HOURS') where username = ?"
        await self.cursor.execute(query_update_last_online, (user.username, ))

    async def get_user_log(self):
        query_get_user_log = "Select username from user"
        await self.cursor.execute(query_get_user_log)
        user_log = []
        while True:
            user = await self.cursor.fetchone()
            if user == None:
                break
            user_log.append(user[0])
        return user_log

    async def close(self):
        await self.connection.close()
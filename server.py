import asyncio
import sys
import datetime
from chat_utils.chatdatabase import ChatDatabase
from chat_utils.chatroom import ChatRoom
from chat_utils.chatroom import User

async def handle(reader, writer):
    username = await chatroom.login(reader, writer)
    if username:
        user = User(writer, username)
    else:
        return
    chatroom.add(user)
    await chatroom.db.get_message_log(writer, username)
    message = f"{user.username!s} is connected !!!!\n"
    await chatroom.broadcast(user, message, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    while True:
        data = (await reader.readline()).decode()
        if reader.at_eof():
            await chatroom.end_user_session(user)
            return
        await chatroom.send_message(user, data)
        

async def main():
    if len(sys.argv) == 3:
        ip = sys.argv[1]
        port = sys.argv[2]
    else:
        print('Correct formatting: script name, IP address, port')
        return
    await chatroom.start_database_server()
    server = await asyncio.start_server(handle, ip, port)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr!s}')
    async with server:
        await server.serve_forever()

chatroom = ChatRoom()
asyncio.run(main())
import asyncio
import sys

import mysql.connector


writers = []

async def forward(sender, username, reciever_username, message):
    is_message = False
    for w in writers:
        if w[1] == reciever_username:
            w[0].write(f"{username!s}: {message!s}\n".encode())
            await w[0].drain()
            is_message = True
    if is_message == False:
        sender.write('No user found'.encode())     
        await sender.drain() 

def broadcast(writer, username, message):
    for w in writers:
        if w[0] != writer:
            w[0].write(f"{username!s}: {message!s}\n".encode())


async def handle(reader, writer):
    username = (await reader.read(20)).decode()
    if username not in [u for w,u in writers]:
    	write_new_user(username)
    message = f"{username!s} is connected !!!!"
    writers.append([writer, username])
    broadcast(writer, username, message)
    await writer.drain()
    while True:
        data = await reader.readline()
        message = data.decode().strip()
        if message[:2] == '/w':
            reciever_username = message.split()[1]
            message_text = message.split(maxsplit = 2)[2]
            write_message(message_text, username)
            await forward(writer, username, reciever_username, message_text)
        else:
            broadcast(writer, username, message)
            await writer.drain()

def write_new_user(username):
    query_user = "Insert into user values('{}');".format(username)
    cnx = mysql.connector.connect(user='root', password='',host='127.0.0.1',database='chat_db')
    cursor = cnx.cursor()
    cursor.execute(query_user)

async def main():
    if len(sys.argv) == 3:
        ip = sys.argv[1]
        port = sys.argv[2]


    else:
        print('Correct formatting: script name, IP address, port')
        exit()
    server = await asyncio.start_server(handle, ip, port)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr!s}')
    async with server:
        await server.serve_forever()

def write_message(message_text, username):
    query_message = "Insert into message values('{0}','{1}');".format(message_text, username)
    cnx = mysql.connector.connect(user='root', password='', host='127.0.0.1', database='chat_db')
    cursor = cnx.cursor()
    cursor.execute(query_message)

asyncio.run(main())
import asyncio, sys, datetime
from aioconsole import ainput

async def get_message_log(reader):
    log_is_not_empty = True
    while log_is_not_empty:
        message = (await reader.readline()).decode()
        if message == '1\n':
            log_is_not_empty = False
        else:
            print(message)

async def send(writer, data):
    writer.write(data.encode())
    await writer.drain()

async def register_user(writer, username):
    print('Username is available')
    print('Set your password (max 255 characters):')
    password = input()
    await send(writer, password)

async def check_user_password(writer,reader, username):
    while True:
        print('Input your password:')
        password = input()
        await send(writer, password)
        code = await reader.read(1)
        if reader.at_eof():
            return False
        if code.decode() == '1': # Пароль верный
            return True
        print('Incorrect password')

async def login(writer, reader):
    while True:
        print('Enter your username(max 20 characters, no spaces):')
        username = input()
        if len(username) < 20 and len(username.split()) == 1:
            await send(writer, username)
            code = (await reader.read(1)).decode()
            if reader.at_eof():
                return False
            if code == '1': # Новый пользователь
                await register_user(writer, username)
                return username
            elif code == '2': # Пользователь уже онлайн
                print('This user has already logged in')
            elif code == '3': # Существующий пользователь
                if await check_user_password(writer, reader, username):
                    return username
                else:
                    return False
        else:    
            print('Incorrect username')

async def _message(writer, reader):
    while True:
        data = await ainput() + '\n'
        if writer.is_closing():
            return
        if data == '\n':
            print('You can not send an empty message')
        else:
            date = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            await send(writer, date + ' ' + data)
            if data[:2] == '/w':
                print(f"[{date}]You (to {data.split()[1]}): {data.split(maxsplit = 2)[2]}")
            else:
                print(f"[{date}]You: {data}")
        

async def _read(writer,reader):
    while True:
        data = await reader.readline()
        if reader.at_eof():
            print('Server Shutdown, press Enter to exit')
            writer.close()
            return
        print(f'{data.decode()!s}')

async def main():
    if len(sys.argv) == 3:
        ip = sys.argv[1]
        port = sys.argv[2]
    else:
        print('Correct formatting: script name, IP address, port')
        return
    reader, writer = await asyncio.open_connection(ip, port)
    username = await login(writer, reader)
    if not username:
        print('Server Shutdown')
        return
    await get_message_log(reader)
    print(f'Welcome to the chat room, {username}!')
    await asyncio.gather(_read(writer, reader), _message(writer, reader))

asyncio.run(main())
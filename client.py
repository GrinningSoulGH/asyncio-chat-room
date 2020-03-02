import asyncio, sys
from aioconsole import ainput

async def _message(writer, reader):
    while True:
        data = (await ainput()) + '\n'
        print(data)
        writer.write(data.encode())
        await writer.drain()
        if data[:2] == '/w':
            print(f"You (to {data.split()[1]}): {data.split(maxsplit = 2)[2]}")
        else:
            print(f"You: {data}")
        

async def _read(reader):
    while True:
        data = await reader.readline()
        print(f'{data.decode()!s}')

async def main():
    if len(sys.argv) == 3:
        ip = sys.argv[1]
        port = sys.argv[2]
    elif len(sys.argv) == 1:
        ip = '127.0.0.1'
        port = '8888'
    else:
        exit()
    reader, writer = await asyncio.open_connection(ip, port)

    print('Enter your username(max 20 characters, no spaces):')
    username = input()
    writer.write(username.encode())
    await writer.drain()
    await asyncio.gather(_read(reader), _message(writer, reader))

asyncio.run(main())
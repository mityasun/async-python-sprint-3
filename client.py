import asyncio

from aioconsole import ainput

from constants import HOST, PORT


class Client:
    def __init__(self, host: str = HOST, port: int = PORT) -> None:
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None

    async def start(self) -> None:
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port
            )
            username = input('Enter your username: ')
            self.writer.write(f'username - {username}'.encode())
            print(f'You are logged in as {username}')
            await asyncio.gather(
                self.send_messages(),
                self.receive_messages()
            )
        except ConnectionRefusedError:
            print(f'Could not connect to {self.host}:{self.port}')

    async def receive_messages(self) -> None:
        while True:
            message = await self.get_message()
            if message == 'exit':
                break
            print(message)

    async def get_message(self) -> str:
        return (await self.reader.read(255)).decode().strip()

    async def send_messages(self) -> None:
        while True:
            message = await ainput(">>> ")
            if message == 'exit':
                self.writer.write('exit'.encode())
                self.writer.close()
                break
            else:
                self.writer.write(f'{message}'.encode())


if __name__ == '__main__':
    client = Client()
    asyncio.run(client.start())

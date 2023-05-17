import asyncio

from aioconsole import ainput

from settings import ChatSettings


class Client:
    def __init__(self, settings: ChatSettings) -> None:
        self.host = settings.HOST
        self.port = settings.PORT
        self.reader = None
        self.writer = None
        self.is_closing = False

    async def start(self) -> None:
        """Start client and connecting to server"""

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

    async def get_message(self) -> str:
        """Get message from server"""

        return (await self.reader.read(255)).decode().strip()

    async def receive_messages(self) -> None:
        """Receive messages from server"""

        try:
            while True:
                message = await self.get_message()
                if self.is_closing:
                    print('Connection closed by user')
                    break
                elif message == 'exit':
                    self.is_closing = True
                else:
                    print(message)
        except (asyncio.IncompleteReadError, ConnectionResetError):
            self.is_closing = True
            print('Connection closed by remote host')
        finally:
            if not self.writer.transport.is_closing():
                self.writer.write('exit'.encode())
                await self.writer.drain()
                self.writer.close()
                await self.writer.wait_closed()

    async def send_messages(self) -> None:
        """Send message to server"""

        while True:
            message = await ainput(">>> ")
            if message == 'exit':
                self.is_closing = True
                self.writer.write('exit'.encode())
                self.writer.close()
                break
            else:
                self.writer.write(f'{message}'.encode())


if __name__ == '__main__':
    client = Client(ChatSettings())
    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        client.is_closing = True
        print('Connection closed by user')

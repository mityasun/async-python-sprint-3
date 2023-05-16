import asyncio


class User:
    def __init__(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter,
            is_public=True
    ):
        self.reader = reader
        self.writer = writer
        self.username = None
        self.reports = 0
        self.is_public = is_public

    async def receive_message(self) -> str:
        return (await self.reader.read(255)).decode().strip()

    def send_message(self, message: str) -> None:
        self.writer.write(message.encode())

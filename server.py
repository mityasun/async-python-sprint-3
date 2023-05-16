import asyncio
import threading
import uuid
from datetime import datetime

from constants import (LAST_MESSAGES, HOST, PORT, MAX_MESSAGE_PER_PERIOD,
                       PERIOD_DURATION, WELCOME, BAN_PERIOD, CHAT_NAME)
from user import User
from utils import logger


class Server:
    def __init__(self, host: str = HOST, port: int = PORT) -> None:
        self.host = host
        self.port = port
        self.public_chat_history = []
        self.users = {}
        self.message_counts = {}
        self.max_messages_per_period = MAX_MESSAGE_PER_PERIOD
        self.period_duration = PERIOD_DURATION
        self.delayed_messages = {}

    async def start(self) -> None:
        """Start chat server"""

        try:
            server = await asyncio.start_server(
                self.client_login, self.host, self.port
            )
            addr = server.sockets[0].getsockname()
            logger.info(f'Started server on {addr}')
            async with server:
                await server.serve_forever()
        except Exception as error:
            logger.info(error)

    async def client_login(
            self,
            reader: asyncio.StreamReader,
            writer: asyncio.StreamWriter
    ) -> None:
        """Create, set username, send last messages."""

        user = User(reader, writer)
        logger.info(f'Create {user}')
        self.set_username(user, await user.receive_message())
        self.users[user.username] = user
        logger.info(f'Add user {user.username} to users list')
        user.send_message(WELCOME)
        logger.info(f'Send welcome to {user.username}')
        await self.send_last_messages(user)
        await self.check_messages(user)

    @staticmethod
    def set_username(user: User, message: str) -> None:
        """Get username from input and set to user object."""

        try:
            username = message.split('-')[-1].strip()
            logger.info(f'Get username from {user}')
            user.username = username
            logger.info(f'Set username to {user}')
        except Exception as error:
            logger.info(error)

    async def send_last_messages(self, user: User) -> None:
        """Create and send last messages from public chat."""

        if len(self.public_chat_history) > 0:
            messages = []
            user.send_message(
                f'The last {LAST_MESSAGES} messages in the public chat:\n'
            )
            num_messages_to_send = min(
                len(self.public_chat_history), LAST_MESSAGES
            )
            messages_to_send = self.public_chat_history[-num_messages_to_send:]
            for message in messages_to_send:
                username, msg = message.split(': ', 1)
                messages.append((username, msg))
            for username, msg in messages:
                user.send_message(f'{username}: {msg} \n')
            logger.info(
                f'Send {LAST_MESSAGES} last messages to {user.username}'
            )
        else:
            user.send_message('Public chat history is empty')
            logger.info(f'Public history is empty for user {user.username}')

    async def check_messages(self, user: User) -> None:
        """Check command before send message"""

        while True:
            message = await user.receive_message()
            if user.reports < 3:
                if message.startswith('username'):
                    self.set_username(user, message)
                elif message.startswith('status'):
                    self.get_chat_status(user)
                elif message.startswith('pm'):
                    self.private_message(message, user)
                elif message.startswith('ban'):
                    self.report(message, user)
                elif message.startswith('delay'):
                    self.delayed_message(message, user)
                elif message.startswith('cancel '):
                    self.cancel_delayed_message(message, user)
                else:
                    self.public_chat(message, user)

    def public_chat(self, message: str, sender: User) -> None:
        """
        Public chat with saving history and
        limiting the number of messages per period.
        """

        now = datetime.now()
        if sender.username not in self.message_counts:
            self.message_counts[sender.username] = {
                'count': 0,
                'last_message_time': now
            }
        else:
            count = self.message_counts[sender.username]['count']
            last_message_time = self.message_counts[sender.username][
                'last_message_time'
            ]
            time_diff = (now - last_message_time).total_seconds()
            if time_diff > self.period_duration:
                count = 0
                logger.info(
                    f'{sender.username} was unblocked after end of period.'
                )
            if count >= self.max_messages_per_period:
                sender.send_message(
                    f'You have reached the maximum number of messages '
                    f'{self.max_messages_per_period} for this period. '
                    f'Please wait until this period is over to send more '
                    f'messages.'
                )
                logger.info(
                    f'{sender.username} was blocked because have reached '
                    f'the maximum number of messages'
                )
            self.message_counts[sender.username]['count'] = count + 1
            self.message_counts[sender.username]['last_message_time'] = now

        self.public_chat_history.append(f'{sender.username}: {message}')
        logger.info('Append public chat history')
        for user in self.users.values():
            if user != sender:
                user.send_message(f'{sender.username}: {message}')
                logger.info(
                    f'Send message from {sender.username} to public chat'
                )

    def get_chat_status(self, sender: User) -> None:
        """Get information about public chat."""

        chat_name = CHAT_NAME
        num_users = len(self.users)
        user_names = ", ".join(self.users.keys())
        message = f'{chat_name}: {num_users} users - {user_names}'
        sender.send_message(message)

    def private_message(self, message: str, sender: User) -> None:
        """Send private message."""

        parts = message.split(' ', 3)
        if len(parts) == 3:
            command, recipient_username, msg = parts
            print(recipient_username)
            recipient = self.users.get(recipient_username)
            print(recipient)
            if recipient:
                recipient.send_message(
                    f'Private message from {sender.username}: {msg}'
                )
                logger.info(
                    f'Send pm from {sender.username} to {recipient_username}'
                )
            else:
                sender.send_message(
                    f'Recipient {recipient_username} not found'
                )
        else:
            sender.send_message(
                'Invalid private message format. Use "pm recipient message"'
            )

    def report(self, message: str, sender: User) -> None:
        """Send ban report to user."""

        parts = message.split(' ', 2)
        if len(parts) == 2:
            reported_user = self.users.get(message.split(' ')[-1].strip())
            if reported_user:
                reported_user.reports += 1
                reported_user.send_message(
                    f'You received a report from a user {sender.username}'
                )
                logger.info(
                    f'{sender.username} send report to '
                    f'{reported_user.username}'
                )
                if reported_user.reports > 2:
                    reported_user.send_message('You have been banned')
                    logger.info(f'{reported_user.username} has been banned.')
                    timer = threading.Timer(BAN_PERIOD, self.unban_user)
                    timer.start()
            else:
                sender.send_message(f'Recipient {reported_user} not found')
        else:
            sender.send_message(
                'Invalid report message format. Use "ban username"'
            )

    @staticmethod
    def unban_user(user: User) -> None:
        """Unban user after end timer."""

        user.send_message(f'{user.username} has been unbanned')
        user.reports = 0
        logger.info(f'{user.username} has been unbanned')

    def delayed_message(self, message: str, user: User) -> None:
        """Set a delay message."""

        try:
            msg = message.split(' ')[1].strip()
            date_str = ' '.join(message.split(' ')[-6:])
            time_obj = None
            try:
                time_obj = datetime.strptime(
                    date_str, '%Y, %m, %d, %H, %M, %S'
                )
            except ValueError:
                user.send_message(
                    'Invalid date format. Use "YYYY, MM, DD, HH, MM, SS"'
                )
            if time_obj is not None:
                msg_id = uuid.uuid4().hex
                delta_seconds = (time_obj - datetime.now()).total_seconds()
                timer = threading.Timer(
                    delta_seconds,
                    self.send_delayed_message,
                    args=(msg_id, msg, user)
                )
                timer.start()
                self.delayed_messages[msg_id] = timer
                user.send_message(
                    f'Scheduled public chat message "{msg}" with ID {msg_id} '
                    f'in {delta_seconds} seconds.'
                )
                logger.info(f'Set delayed message for user {user.username}.')
        except IndexError:
            user.send_message(
                'Invalid delayed message format. '
                'Use "delay text YYYY, MM, DD, HH, MM, SS"'
            )

    def send_delayed_message(
            self, msg_id: str, message: str, user: User
    ) -> None:
        """Send delayed message after end timer."""

        if msg_id in self.delayed_messages:
            del self.delayed_messages[msg_id]
            self.public_chat(message, user)
            user.send_message(
                f'Delayed message with ID {msg_id} was send in chat.'
            )
            logger.info(f'Delayed message with ID {msg_id} was send in chat.')
        else:
            user.send_message(
                f'Delayed message with ID {msg_id} has already '
                f'been cancelled or sent.'
            )

    def cancel_delayed_message(self, message: str, user: User) -> None:
        """Cancel delayed message before it will be sent"""

        parts = message.split(' ', 2)
        if len(parts) == 2:
            msg_id = message.split(' ')[-1].strip()
            if msg_id in self.delayed_messages:
                self.delayed_messages[msg_id].cancel()
                del self.delayed_messages[msg_id]
                user.send_message(
                    f'Delayed message with ID {msg_id} has been cancelled.'
                )
                logger.info(f'User {user.username} cancel delayed message')
            else:
                user.send_message(
                    f'Delayed message with ID {msg_id} not found.'
                )
        else:
            user.send_message(
                'Invalid cancel delayed message format. Use "cancel id"'
            )


if __name__ == '__main__':
    server = Server()
    asyncio.run(server.start())

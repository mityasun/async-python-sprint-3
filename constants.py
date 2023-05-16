HOST: str = '127.0.0.1'
PORT: int = 8000
CHAT_NAME: str = 'Public chat'
LAST_MESSAGES: int = 20
MAX_MESSAGE_PER_PERIOD: int = 20
PERIOD_DURATION: int = 3600
BAN_PERIOD: int = 14400
WELCOME: str = (
    f'Welcome to {CHAT_NAME}. You can use following commands: \n'
    f'status - get information about public chat. \n'
    f'pm username text - to send private message. \n'
    f'ban username - to send a report to user. \n'
    f'delay text YYYY, MM, DD, HH, MM, SS - send a delayed message. \n'
    f'cancel id - cancel a delayed message. \n'
    f'exit - leave the chat. \n'
)

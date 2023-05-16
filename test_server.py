from datetime import datetime
from unittest.mock import Mock, patch, call

import pytest

from constants import LAST_MESSAGES
from server import Server


@pytest.fixture(scope='function')
def server():
    return Server()


@patch('server.User.receive_message')
def test_set_username(mock_receive_message):
    """Test set username"""

    user = Mock()
    message = 'username - test'
    mock_receive_message.return_value = message
    Server.set_username(user, message)
    assert user.username == 'test'


@pytest.mark.asyncio
async def test_send_last_messages(server):
    """Test send last messages"""

    user1 = Mock()
    user2 = Mock()
    server.users = {'user1': user1, 'user2': user2}
    server.public_chat_history = ['user1: hello', 'user2: world']

    await server.send_last_messages(user1)

    user1.send_message.assert_has_calls(
        [
            call(f'The last {LAST_MESSAGES} messages in the public chat:\n'),
            call('user1: hello \n'),
            call('user2: world \n')
        ]
    )
    user2.send_message.assert_not_called()


def test_public_chat(server):
    """Test send message to chat"""

    user = Mock()
    message = 'username - user'
    server.set_username(user, message)
    server.max_messages_per_period = 3
    server.period_duration = 60
    now = datetime.now()

    server.public_chat('hello', user)
    assert server.public_chat_history == ['user: hello']
    assert server.message_counts == {
        'user': {'count': 0, 'last_message_time': now}
    }

    server.public_chat('world', user)
    assert server.public_chat_history == ['user: hello', 'user: world']
    assert server.message_counts == {
        'user': {'count': 1, 'last_message_time': now}
    }


def test_private_message(server):
    """Test private messages"""

    sender = Mock(username='sender')
    recipient = Mock(username='recipient')
    server.users = {'sender': sender, 'recipient': recipient}

    server.private_message('pm recipient hello', sender)

    recipient.send_message.assert_called_once_with(
        'Private message from sender: hello'
    )


def test_report(server):
    """Test ban report"""

    sender = Mock(username='sender')
    reported_user = Mock(username='reported_user')
    reported_user.reports = 0
    server.users = {'sender': sender, 'reported_user': reported_user}
    server.report('ban reported_user', sender)
    assert reported_user.reports == 1

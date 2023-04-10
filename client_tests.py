from client import ChatClient
from commands import *
from unittest.mock import MagicMock
from unittest.mock import patch
from io import StringIO

# pytest client_tests.py

def test_registration_flow():
    # Testing registration flow
    client = ChatClient(test=True)

    # Setting up mocks
    client.logged_in = False
    client.username = None
    client.connection = MagicMock()
    client.connection.register_user = MagicMock(return_value=MagicMock(text=LOGIN_SUCCESSFUL))

    # Test registration
    with patch("builtins.input", side_effect=["0", "dale"]):
        assert not client.logged_in
        assert not client.username

        client.login()

        client.connection.register_user.assert_called_once()
        assert client.logged_in
        assert client.username == "dale"


def test_login_flow():
    # Testing login flow
    client = ChatClient(test=True)

    # Setting up mocks
    client.logged_in = False
    client.username = None
    client.connection = MagicMock()
    client.connection.login_user = MagicMock(return_value=MagicMock(text=LOGIN_SUCCESSFUL))

    # Test registration
    with patch("builtins.input", side_effect=["1", "dale"]):
        assert not client.logged_in
        assert not client.username

        client.login()

        client.connection.login_user.assert_called_once()
        assert client.logged_in
        assert client.username == "dale"


def test_display_accounts():
    # Testing display accounts
    client = ChatClient(test=True)

    # Setting up mocks
    client.connection = MagicMock()
    client.connection.display_accounts = MagicMock(return_value=[MagicMock(text="dale"), MagicMock(text="dallen")])

    # Test registration
    with patch("builtins.input", side_effect=["dale"]):
        with patch('sys.stdout', new = StringIO()) as terminal_output:
            client.display_accounts()
            client.connection.display_accounts.assert_called_once()

            assert terminal_output.getvalue() == "\nUsers:\ndale\ndallen\n"


def test_send_message():
    # Testing send message
    client = ChatClient(test=True)

    # Setting up mocks
    client.username = "alyssa"
    client.connection = MagicMock()
    client.connection.check_user_exists = MagicMock(return_value=MagicMock(text=""))
    client.connection.client_send_message = MagicMock(return_value=MagicMock(text="Message sent!"))

    # Test registration
    with patch("builtins.input", side_effect=["dale", "hi dale"]):
        with patch('sys.stdout', new = StringIO()) as terminal_output:
            client.send_chat_message()
            client.connection.client_send_message.assert_called_once()

            assert terminal_output.getvalue() == "Message sent!\n"


def test_delete_flow():
    # Testing delete flow
    client = ChatClient(test=True)

    # Setting up mocks
    client.logged_in = True
    client.username = "dale"
    client.connection = MagicMock()
    client.connection.delete_account = MagicMock(return_value=MagicMock(text=DELETION_SUCCESSFUL))
    client.login = MagicMock(return_value=None)

    # Test registration
    with patch("builtins.input", side_effect=["0", "dale"]):
        assert client.logged_in
        assert client.username

        client.delete_or_logout()

        client.connection.delete_account.assert_called_once()
        assert not client.logged_in
        assert not client.username


def test_logout_flow():
    # Testing logout flow
    client = ChatClient(test=True)

    # Setting up mocks
    client.logged_in = True
    client.username = "dale"
    client.connection = MagicMock()
    client.connection.logout = MagicMock(return_value=MagicMock(text=LOGOUT_SUCCESSFUL))
    client.login = MagicMock(return_value=None)

    # Test registration
    with patch("builtins.input", side_effect=["1", "dale"]):
        assert client.logged_in
        assert client.username

        client.delete_or_logout()

        client.connection.logout.assert_called_once()
        assert not client.logged_in
        assert not client.username
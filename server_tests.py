from server import ChatServicer
from commands import *
from unittest.mock import MagicMock
from unittest.mock import patch
import new_route_guide_pb2
from io import StringIO

# pytest server_tests.py

def test_persistence():
    # Testing persistence
    server = ChatServicer(logfile="test_persistence.log")

    assert len(server.accounts) == 2
    assert "alyssa" in server.accounts
    assert "maegan" in server.accounts
    assert "alyssa" in server.unsent_messages
    assert len(server.unsent_messages["alyssa"]) == 1
    assert server.unsent_messages["alyssa"][0] == ('maegan', "hi hanging")


def test_backup_sync():
    # Testing backup sync
    server = ChatServicer(port=1050)

    server.replica_client_receive_message = MagicMock()
    server.client_send_message = MagicMock()

    server.backup_connections = {"test_backup": 1051}

    # No hanging message logged
    new_server = ChatServicer(logfile="1051.log")
    assert "alyssa" in new_server.unsent_messages
    assert len(new_server.unsent_messages["alyssa"]) == 0

    # Test backup sync
    server.sync_backups()

    server.client_send_message.assert_called_once()
    server.replica_client_receive_message.assert_called_once()


def test_login_flow():
    # Testing login flow
    server = ChatServicer()

    # Setting up mocks
    new_route_guide_pb2.Text=MagicMock()
    request = MagicMock()
    request.text = "dale"

    # Test username does not exist
    assert len(server.accounts) == 0
    server.login_user(request, None)
    new_route_guide_pb2.Text.assert_called_with(text="Username does not exist.")

    # Test user already logged in
    server.accounts.append("dale")
    server.active_accounts["dale"] = "mock ip address"

    server.login_user(request, None)
    new_route_guide_pb2.Text.assert_called_with(text="User is already logged in.")

    # Test successful login
    server.active_accounts = {}
    assert len(server.accounts) == 1

    server.login_user(request, None)
    new_route_guide_pb2.Text.assert_called_with(text=LOGIN_SUCCESSFUL)


def test_registration_flow():
    # Testing registration flow
    server = ChatServicer()

    # Setting up mocks
    new_route_guide_pb2.Text=MagicMock()
    request = MagicMock()
    request.text = "dale"

    # Test username already exists
    server.accounts.append("dale")
    assert len(server.accounts) == 1

    server.register_user(request, None)
    new_route_guide_pb2.Text.assert_called_with(text="Username already exists.")

    # Test successful login
    server.accounts = []

    server.register_user(request, None)
    assert len(server.accounts) == 1
    assert server.accounts[0] == "dale"
    
    assert "dale" in server.active_accounts
    
    assert "dale" in server.unsent_messages

    new_route_guide_pb2.Text.assert_called_with(text=LOGIN_SUCCESSFUL)


def test_check_user_exists_flow():
    # Testing registration flow
    server = ChatServicer()

    # Setting up mocks
    new_route_guide_pb2.Text=MagicMock()
    request = MagicMock()
    request.text = "dale"

    # Test username does not exist
    assert len(server.accounts) == 0
    server.check_user_exists(request, None)
    new_route_guide_pb2.Text.assert_called_with(text=USER_DOES_NOT_EXIST)

    # Test successful find
    server.accounts.append("dale")
    server.check_user_exists(request, None)
    new_route_guide_pb2.Text.assert_called_with(text="User exists.")


def test_client_receive_message_flow():
    # Testing client receive message flow
    server = ChatServicer()

    # Setting up mocks
    new_route_guide_pb2.Text=MagicMock()
    request = MagicMock()
    request.text = "dale"
    server.unsent_messages["dale"] = [("alyssa", "hi dale 1"), ("alyssa", "hi dale 2")]

    # Test client send message
    server.replica_client_receive_message(request, None)

    assert "dale" in server.unsent_messages
    assert len(server.unsent_messages["dale"]) == 0

    new_route_guide_pb2.Text.assert_called_with(text=UPDATE_SUCCESSFUL)


def test_client_send_message_flow():
    # Testing client send message flow
    server = ChatServicer()

    # Setting up mocks
    new_route_guide_pb2.Text=MagicMock()
    request = MagicMock()
    request.recipient = "dale"
    request.sender = "alyssa"
    request.message = "hi dale"
    server.unsent_messages["dale"] = []

    # Test client send message
    server.client_send_message(request, None)

    assert "dale" in server.unsent_messages
    assert len(server.unsent_messages["dale"]) == 1
    assert server.unsent_messages["dale"][0][0] == "alyssa"
    assert server.unsent_messages["dale"][0][1] == "hi dale"

    new_route_guide_pb2.Text.assert_called_with(text="Message sent!")


def test_delete_account_flow():
    # Testing delete account flow
    server = ChatServicer()

    # Setting up mocks
    new_route_guide_pb2.Text=MagicMock()
    request = MagicMock()
    request.text = "dale"

    # Test delete account
    server.accounts.append("dale")
    server.active_accounts["dale"] = "mock ip address"
    server.unsent_messages["dale"] = ["hi dale 1", "hi dale 2"]

    server.delete_account(request, None)

    assert len(server.accounts) == 0
    assert "dale" not in server.active_accounts
    assert "dale" not in server.unsent_messages

    new_route_guide_pb2.Text.assert_called_with(text=DELETION_SUCCESSFUL)


def test_logout_flow():
    # Testing logout flow
    server = ChatServicer()

    # Setting up mocks
    new_route_guide_pb2.Text=MagicMock()
    request = MagicMock()
    request.text = "dale"

    # Test account account
    server.accounts.append("dale")
    server.active_accounts["dale"] = "mock ip address"
    server.unsent_messages["dale"] = ["hi dale 1", "hi dale 2"]

    server.logout(request, None)

    assert "dale" in server.accounts
    assert "dale" not in server.active_accounts
    assert "dale" in server.unsent_messages

    new_route_guide_pb2.Text.assert_called_with(text=LOGOUT_SUCCESSFUL)
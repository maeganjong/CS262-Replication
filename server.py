import grpc
from grpc._server import _Server
import new_route_guide_pb2
import new_route_guide_pb2_grpc

import socket 
import threading
from concurrent import futures
import re
from commands import *

import threading

mutex_unsent_messages = threading.Lock()
mutex_accounts = threading.Lock()
mutex_active_accounts = threading.Lock()

class ChatServicer(new_route_guide_pb2_grpc.ChatServicer):
    '''Initializes ChatServicer that sets up the datastructures to store user accounts and messages.'''
    def __init__(self, port):
        self.port = port

        self.unsent_messages = {} # {username: [msg1, msg2, msg3]}
        self.accounts = [] # [username1, username2, username3]
        self.active_accounts = {} # {username: addr}

        self.is_leader = False
        self.backup_connections = {} # len 1 if a backup, len 2 if leader
        self.leader_connection = None # None if leader, connection to leader if backup
    

    def connect_to_replicas(self, port1, port2):
        # TODO: WRAP THINGS IN TRY CATCHES
        if min(self.port, port1, port2) == self.port:
            self.is_leader = True
            print("I am the leader")
            connection1 = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{SERVER}:{port1}"))
            connection2 = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{SERVER}:{port2}"))
            self.backup_connections[connection1] = port1
            self.backup_connections[connection2] = port2
        
        else:
            print("I am a backup")
            if min(self.port, port1, port2) == port1:
                self.leader_connection = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{SERVER}:{port1}"))
                self.backup_connections[self.leader_connection] = port2
            else:
                self.leader_connection = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{SERVER}:{port2}"))
                self.backup_connections[self.leader_connection] = port1
        
        # try:
        #     # TODO: Ping other replicas to test connection
        #     ## DOES NOT WORK - CAUSES RECURSIVE SERVER ERRORS
        #     new_text = new_route_guide_pb2.Text()
        #     new_text.text = IS_ALIVE

        #     if self.is_leader:
        #         response = connection1.alive_ping(new_text)
        #         print("Backup 1: ", response)

        #         response = connection2.alive_ping(new_text)
        #         print("Backup 2: ", response)
        #     else:
        #         response = self.leader_connection.alive_ping(new_text)
        #         print("Leader: ", response)
                
        #         # THIS DOESN'T WORK CAUSE port1/port2 AREN'T CHATSTUBS
        #         # response = self.backup_connections[self.leader_connection].alive_ping(new_text)
        #         # print("Other backup: ", response)
        # except Exception as e:
        #     # Retry connecting to other replicas
        #     print("ERROR - check connect_to_replicas method")
        #     self.connect_to_replicas(port1, port2)
    
    
    def ping_leader(self):
        if self.is_leader:
            return
        
        try:
            # TODO: THIS IS FAKE JUST CHECKING IF WE CAN PING OTHERS
            # TODO: DEFINE SOME NEW GRPC PROTOBUF THINGY FUNCTION??? TO PING
            # HAS BEEN ADDRESSED
            new_text = new_route_guide_pb2.Text()
            new_text.text = IS_ALIVE
            response = self.leader_connection.alive_ping(new_text)
            print(response)
        except:
            print("Leader is down")

    '''Determines whether the user is currently in the registered list of users.'''
    def alive_ping(self):
        return new_route_guide_pb2.Text(text=LEADER_ALIVE)


    '''Logins the user by checking the list of accounts stored in the server session.'''
    def login_user(self, request, context):
        print("Logging in user")
        username = request.text
        
        if username not in self.accounts:
            return new_route_guide_pb2.Text(text="Username does not exist.")
        elif username in self.active_accounts:
            return new_route_guide_pb2.Text(text="User is already logged in.")
        else:
            # Log in user
            mutex_active_accounts.acquire()
            self.active_accounts[username] = context.peer()
            mutex_active_accounts.release()
        
        # If leader, sync replicas
        if self.is_leader:
            print("Updating backups...")
            new_text = new_route_guide_pb2.Text()
            new_text.text = username
            for replica in self.backup_connections:
                response = None
                # Block until backups have been successfully updated
                while not response or response.text != LOGIN_SUCCESSFUL:
                    response = replica.login_user(new_text)
        
        return new_route_guide_pb2.Text(text=LOGIN_SUCCESSFUL)

    '''Registers user given the client's input and compares with existing account stores.'''
    def register_user(self, request, context):
        username = request.text
        if username in self.accounts:
            return new_route_guide_pb2.Text(text="Username already exists.")
        else:
            print(f"Registering {username}")
            # Register and log in user
            mutex_active_accounts.acquire()
            self.active_accounts[username] = context.peer()
            mutex_active_accounts.release()

            mutex_accounts.acquire()
            self.accounts.append(username)
            mutex_accounts.release()

            mutex_unsent_messages.acquire()
            self.unsent_messages[username] = []
            mutex_unsent_messages.release()

            # If leader, sync replicas
            if self.is_leader:
                print("Updating backups...")
                new_text = new_route_guide_pb2.Text()
                new_text.text = username
                for replica in self.backup_connections:
                    response = None
                    # Block until backups have been successfully updated
                    while not response or response.text != LOGIN_SUCCESSFUL:
                        response = replica.register_user(new_text)
                        
            return new_route_guide_pb2.Text(text=LOGIN_SUCCESSFUL)
        
    '''Determines whether the user is currently in the registered list of users.'''
    def check_user_exists(self, request, context):
        username = request.text
        if username in self.accounts:
            return new_route_guide_pb2.Text(text="User exists.")
        else:
            return new_route_guide_pb2.Text(text=USER_DOES_NOT_EXIST)
        
    '''Handles the clients receiving messages sent to them. Delivers the message to the clients then clears sent messages'''
    def client_receive_message(self, request, context):
        lastindex = 0
        recipient = request.text
        mutex_unsent_messages.acquire()
        while len(self.unsent_messages[recipient]) > lastindex:
            sender, message = self.unsent_messages[recipient][lastindex]
            lastindex += 1
            formatted_message = new_route_guide_pb2.Note()
            formatted_message.recipient = recipient
            formatted_message.sender = sender
            formatted_message.message = message
            yield formatted_message
        mutex_unsent_messages.release()
        self.unsent_messages[recipient] = []

        # If leader, sync replicas
        if self.is_leader:
            print("Updating backups...")
            # TODO: UPDATE YIELD IS BEING WEIRD IDK

        return new_route_guide_pb2.Text(text=UPDATE_SUCCESSFUL)

    '''Handles the clients sending messages to other clients'''
    def client_send_message(self, request, context):
        recipient = request.recipient
        sender = request.sender
        message = request.message
        mutex_unsent_messages.acquire()
        self.unsent_messages[recipient].append((sender, message))
        mutex_unsent_messages.release()

        # If leader, sync replicas
        if self.is_leader:
            print("Updating backups...")
            new_message = new_route_guide_pb2.Note()
            new_message.sender = sender
            new_message.recipient = recipient
            new_message.message = message
            for replica in self.backup_connections:
                response = None
                # Block until backups have been successfully updated
                while not response or response.text != SEND_SUCCESSFUL:
                    response = replica.client_send_message(new_message)

        return new_route_guide_pb2.Text(text=SEND_SUCCESSFUL)

    '''Deletes the account for the client requesting the deletion'''
    def delete_account(self, request, context):
        username = request.text
        try: 
            mutex_active_accounts.acquire()
            del self.active_accounts[username]
            mutex_active_accounts.release()

            mutex_unsent_messages.acquire()
            del self.unsent_messages[username]
            mutex_unsent_messages.release()

            mutex_accounts.acquire()
            self.accounts.remove(username)
            mutex_accounts.release()
        except:
            return new_route_guide_pb2.Text(text=DELETION_UNSUCCESSFUL)

        # If leader, sync replicas
        if self.is_leader:
            print("Updating backups...")
            new_text = new_route_guide_pb2.Text()
            new_text.text = username
            for replica in self.backup_connections:
                response = None
                # Block until backups have been successfully updated
                while not response or response.text != DELETION_SUCCESSFUL:
                    response = replica.delete_account(new_text)
        
        return new_route_guide_pb2.Text(text=DELETION_SUCCESSFUL)
    
    '''Displays the current registered accounts that match the regex expression given by the client'''
    def display_accounts(self, request, context):
        none_found = True
        username = request.text
        for account in self.accounts:
            x = re.search(username, account)
            if x is not None:
                none_found = False
                yield new_route_guide_pb2.Text(text = x.string)
        if none_found:
            yield new_route_guide_pb2.Text(text = "No user matches this!")

    '''Logs out the user. Assumes that the user is already logged in and is displayed as an active account'''
    def logout(self, request, context):
        username = request.text
        mutex_active_accounts.acquire()
        del self.active_accounts[username]
        mutex_active_accounts.release()

        # If leader, sync replicas
        if self.is_leader:
            print("Updating backups...")
            new_text = new_route_guide_pb2.Text()
            new_text.text = username
            for replica in self.backup_connections:
                response = None
                # Block until backups have been successfully updated
                while not response or response.text != LOGOUT_SUCCESSFUL:
                    response = replica.logout(new_text)

        return new_route_guide_pb2.Text(text=LOGOUT_SUCCESSFUL)

"""Class for running server backend functionality."""
class ServerRunner:
    """Initialize a server instance."""
    def __init__(self, ip = "localhost", port = 8050):
        self.ip = SERVER
        self.port = port

        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.chat_servicer = ChatServicer(self.port)
    
    """Function for starting server."""
    def start(self):
        new_route_guide_pb2_grpc.add_ChatServicer_to_server(self.chat_servicer, self.server)
        self.server.add_insecure_port(f"[::]:{self.port}")
        self.server.start()

    """Function for waiting for server termination."""
    def wait_for_termination(self):
        self.server.wait_for_termination()
    
    """Function for connecting to replicas."""
    def connect_to_replicas(self, port1, port2):
        self.chat_servicer.connect_to_replicas(port1, port2)

    """Function for stopping server."""
    def stop(self):
        self.server.stop(grace=None)
        self.thread_pool.shutdown(wait=False)


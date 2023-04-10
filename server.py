import grpc
from grpc._server import _Server
import new_route_guide_pb2
import new_route_guide_pb2_grpc

import socket 
import threading
from concurrent import futures
import re
from commands import *

import logging

import threading

mutex_unsent_messages = threading.Lock()
mutex_accounts = threading.Lock()
mutex_active_accounts = threading.Lock()

class ChatServicer(new_route_guide_pb2_grpc.ChatServicer):
    '''Initializes ChatServicer that sets up the datastructures to store user accounts and messages.'''
    def __init__(self, port, logfile = None):
        self.port = port

        self.unsent_messages = {} # {username: [msg1, msg2, msg3]}
        self.accounts = [] # [username1, username2, username3]
        self.active_accounts = {} # {username: addr}

        self.is_leader = False
        self.backup_connections = {} # len 1 if a backup, len 2 if leader (at start)
        self.leader_connection = None # None if leader, connection to leader if backup

        logging.basicConfig(filename=f'{port}.log', encoding='utf-8', level=logging.DEBUG, filemode="w")

        if logfile:
            # Persistence: all servers went down and set up this server from the log file
            self.set_state_from_file(logfile)
    

    def process_line(self, line):
        header = "INFO:root:"
        if line.startswith(header):
                line = line[len(header):]
                line = line[:-1] # remove newline char at end of string
        parsed_line = line.split(SEPARATOR)
        
        purpose = parsed_line[0]
        if purpose == LOGIN_SUCCESSFUL:
            username = parsed_line[1]
            request = new_route_guide_pb2.Text()
            request.text = username

            self.login_user(request, None)
        elif purpose == REGISTRATION_SUCCESSFUL:
            username = parsed_line[1]
            request = new_route_guide_pb2.Text()
            request.text = username

            self.register_user(request, None)
        elif purpose == SEND_SUCCESSFUL:
            sender = parsed_line[1]
            recipient = parsed_line[2]
            message = SEPARATOR.join(parsed_line[3:])

            request = new_route_guide_pb2.Note()
            request.sender = sender
            request.recipient = recipient
            request.message = message

            self.client_send_message(request, None)
        elif purpose == UPDATE_SUCCESSFUL:
            username = parsed_line[1]
            request = new_route_guide_pb2.Text()
            request.text = username

            self.client_receive_message(request, None)
        elif purpose == DELETION_UNSUCCESSFUL:
            username = parsed_line[1]
            request = new_route_guide_pb2.Text()
            request.text = username

            self.delete_account(request, None)
        elif purpose == LOGOUT_SUCCESSFUL:
            username = parsed_line[1]
            request = new_route_guide_pb2.Text()
            request.text = username

            self.logout(request, None)
    

    def set_state_from_file(self, logfile):
        # Every server should act like a backup server at this point (no updating others just itself)
        f = open(logfile, "r")
        for line in f:
            self.process_line(line)

        f.close()

    def connect_to_replicas(self, address1, address2):
        # TODO: WRAP THINGS IN TRY CATCHES
        server1, port1 = address1
        server2, port2 = address2
        if min(self.port, port1, port2) == self.port:
            self.is_leader = True
            print("I am the leader")
            connection1 = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{server1}:{port1}"))
            connection2 = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{server2}:{port2}"))
            self.backup_connections[connection1] = port1
            self.backup_connections[connection2] = port2
            logging.info(f"Leader")
        
        else:
            print("I am a backup")
            if min(self.port, port1, port2) == port1:
                self.leader_connection = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{server1}:{port1}"))
                other_replica = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{server2}:{port2}"))
                self.backup_connections[other_replica] = port2
            else:
                self.leader_connection = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{server2}:{port2}"))
            logging.info(f"Backup")
        
        print("Connected to replicas")
        logging.info(f"Connected to replicas")


    '''Determines whether server being pinged is alive and can respond.'''
    def alive_ping(self, request, context):
        return new_route_guide_pb2.Text(text=LEADER_ALIVE)
    

    """Notify the server that they are the new leader."""
    def notify_leader(self, request, context):
        self.sync_backups()
        print("Backup syncing is done")
        self.is_leader = True
        logging.info(f"This server is now the new leader")
        return new_route_guide_pb2.Text(text=LEADER_CONFIRMATION)


    """Syncs the backups with the new leader's state."""
    def sync_backups(self):
        # Operates on the assumption that the new leader is the first (of all the backups) to sync with ex-leader
        # Send all accounts to backups
        new_leader_log_file = f'{self.port}.log'
        for replica in self.backup_connections:
            replica_log_file = f'{self.backup_connections[replica]}.log'
            
            lines1 = list(open(new_leader_log_file, "r"))
            lines2 = list(open(replica_log_file, "r"))

            if len(lines1) != len(lines2):
                # Not synced; lines1 must have more lines
                print(lines1[len(lines2):])
                for unsynced_line in lines1[len(lines2):]:
                    self.process_line(unsynced_line)

        logging.info(f"Backups synced")


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
            # self.active_accounts[username] = context.peer()
            # TODO: check this?
            self.active_accounts[username] = None
            mutex_active_accounts.release()
        
        # If leader, sync replicas
        if self.is_leader:
            logging.info(f"Updating backups...")
            new_text = new_route_guide_pb2.Text()
            new_text.text = username
            for replica in self.backup_connections:
                response = None
                # Block until backups have been successfully updated
                try:
                    response = replica.login_user(new_text)
                except Exception as e:
                    print("Backup is down")
                    break
        
        logging.info(LOGIN_SUCCESSFUL + SEPARATOR + username)
        
        return new_route_guide_pb2.Text(text=LOGIN_SUCCESSFUL)

    '''Registers user given the client's input and compares with existing account stores.'''
    def register_user(self, request, context):
        username = request.text
        # Additional check for log reading in persistence
        if SEPARATOR in username:
            return new_route_guide_pb2.Text(text="Username cannot contain the character: {SEPARATOR}")
        
        if username in self.accounts:
            return new_route_guide_pb2.Text(text="Username already exists.")
        else:
            print(f"Registering {username}")
            # Register and log in user
            mutex_active_accounts.acquire()
            # TODO: check this?
            self.active_accounts[username] = None
            # self.active_accounts[username] = context.peer()
            mutex_active_accounts.release()

            mutex_accounts.acquire()
            self.accounts.append(username)
            mutex_accounts.release()

            mutex_unsent_messages.acquire()
            self.unsent_messages[username] = []
            mutex_unsent_messages.release()

            # If leader, sync replicas
            if self.is_leader:
                logging.info(f"Updating backups...")
                new_text = new_route_guide_pb2.Text()
                new_text.text = username
                for replica in self.backup_connections:
                    response = None
                    # Block until backups have been successfully updated
                    try:
                        response = replica.register_user(new_text)
                    except Exception as e:
                        print("Backup is down")
                        break
            
            logging.info(REGISTRATION_SUCCESSFUL + SEPARATOR + username)

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

        # TODO: THIS NEEDS TO BE MOVED FOR THE SAKE OF PERSISTENCE TTESTIGN HERE FOR NOW; so that backups also have it!!
        logging.info(UPDATE_SUCCESSFUL + SEPARATOR + recipient)

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
            # TODO: CHECK THIS?
            # AN ATTEMPT: because of other issues, can't really test rn. Basically, instead of yielding for backups, 
            # I create another grpc method that just tells the replicas to clear unssent_messages
            # TODO: add logging for this
            for connection in self.backup_connections:
                try:
                    # TODO: HANDLE DIFFEENTLY
                    response = connection.replica_client_receive_message(request)
                    if response.text != UPDATE_SUCCESSFUL:
                        print("error with update backup")
                except Exception as e:
                    print("Backup is down")
                    break

            # TODO: UPDATE YIELD IS BEING WEIRD IDK

        return new_route_guide_pb2.Text(text=UPDATE_SUCCESSFUL)
    
    def replica_client_receive_message(self, request, context):
        recipient = request.text
        mutex_unsent_messages.acquire()
        self.unsent_messages[recipient] = []
        mutex_unsent_messages.release()
        logging.info(UPDATE_SUCCESSFUL + SEPARATOR + recipient)
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
            logging.info(f"Updating backups...")
            new_message = new_route_guide_pb2.Note()
            new_message.sender = sender
            new_message.recipient = recipient
            new_message.message = message
            for replica in self.backup_connections:
                response = None
                # Block until backups have been successfully updated
                try:
                    response = replica.client_send_message(new_message)
                except Exception as e:
                    print("Backup is down")
                    break
        
        logging.info(SEND_SUCCESSFUL + SEPARATOR + sender + SEPARATOR + recipient + SEPARATOR + message)

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
            logging.info(f"Updating backups...")
            new_text = new_route_guide_pb2.Text()
            new_text.text = username
            for replica in self.backup_connections:
                response = None
                # Block until backups have been successfully updated
                try:
                    response = replica.delete_account(new_text)
                except Exception as e:
                    print("Backup is down")
                    break

        logging.info(DELETION_SUCCESSFUL + SEPARATOR + username)
        
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
            logging.info(f"Updating backups...")
            new_text = new_route_guide_pb2.Text()
            new_text.text = username
            for replica in self.backup_connections:
                response = None
                # Block until backups have been successfully updated
                try:
                    response = replica.logout(new_text)
                except Exception as e:
                    print("Backup is down")
                    break
        
        logging.info(LOGOUT_SUCCESSFUL + SEPARATOR + username)

        return new_route_guide_pb2.Text(text=LOGOUT_SUCCESSFUL)

"""Class for running server backend functionality."""
class ServerRunner:
    """Initialize a server instance."""
    def __init__(self, ip = "localhost", port = 8050, logfile=None):
        self.ip = ip
        self.port = port

        self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
        self.chat_servicer = ChatServicer(self.port, logfile=logfile)
    
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


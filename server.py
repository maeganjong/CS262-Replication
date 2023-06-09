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
    def __init__(self, port=8050, logfile = None):
        self.port = port

        self.unsent_messages = {} # {username: [msg1, msg2, msg3]}
        self.accounts = [] # [username1, username2, username3]
        self.active_accounts = {} # {username: addr}

        self.is_leader = False
        self.backup_connections = {} # len 1 if a backup, len 2 if leader (at start)
        self.other_servers = {} # for logging purposes

        # Sets up logging functionality
        self.setup_logger(f'{PORT1}', f'{PORT1}.log')
        self.setup_logger(f'{PORT2}', f'{PORT2}.log')
        self.setup_logger(f'{PORT3}', f'{PORT3}.log')
        
        if logfile:
            # Persistence: all servers went down and set up this server from the log file
            self.set_state_from_file(logfile)

    '''Initializes the logging meta settings'''
    def setup_logger(self, logger_name, log_file, level=logging.INFO):
        l = logging.getLogger(logger_name)
        formatter = logging.Formatter('%(message)s')
        fileHandler = logging.FileHandler(log_file, mode='w')
        fileHandler.setFormatter(formatter)
        streamHandler = logging.StreamHandler()
        streamHandler.setFormatter(formatter)

        l.setLevel(level)
        l.addHandler(fileHandler)
        l.addHandler(streamHandler) 

    '''Server sends its log writes to other replicas so all machines have same set of log files'''
    def log_update(self, request, context):
        machine = request.sender
        log_message = request.message
        logger = logging.getLogger(machine)
        logger.info(log_message)
        return new_route_guide_pb2.Text(text="Done")
        
    '''Processes log files for starting the persistence server'''
    def process_line(self, line):
        header = "INFO:root:"
        line = line[:-1] # remove newline char at end of string
        if line.startswith(header):
                line = line[len(header):]
        parsed_line = line.split(SEPARATOR)
        
        purpose = parsed_line[0]
        # Handles all actions and replicates in the new server
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

            self.replica_client_receive_message(request, None)
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
    
    '''Sets up a server from the log file'''
    def set_state_from_file(self, logfile):
        f = open(logfile, "r")
        for line in f:
            self.process_line(line)

        f.close()

    '''Connects each replica based on the hierarchy of backups'''
    def connect_to_replicas(self, address1, address2):
        if self.port == PORT1:
            self.is_leader = True
            print("I am the leader")
            connection1 = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{SERVER2}:{PORT2}"))
            connection2 = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{SERVER3}:{PORT3}"))
            self.backup_connections[connection1] = PORT2
            self.backup_connections[connection2] = PORT3
            self.other_servers[connection1] = PORT2
            self.other_servers[connection2] = PORT3
            
        elif self.port == PORT2:
            print("I am a backup 8051")
            connection1 = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{SERVER1}:{PORT1}"))
            connection3 = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{SERVER3}:{PORT3}"))
            self.backup_connections[connection3] = PORT3
            self.other_servers[connection1] = PORT1
            self.other_servers[connection3] = PORT3
        else:
            print("I am a backup 8052")
            connection1 = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{SERVER1}:{PORT1}"))
            connection2 = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{SERVER2}:{PORT2}"))
            self.other_servers[connection1] = PORT1
            self.other_servers[connection2] = PORT2
        
        print("Connected to replicas")

    '''Determines whether server being pinged is alive and can respond.'''
    def alive_ping(self, request, context):
        return new_route_guide_pb2.Text(text=LEADER_ALIVE)

    """Notify the server that they are the new leader."""
    def notify_leader(self, request, context):
        self.sync_backups()
        print("Backup syncing is done")
        self.is_leader = True
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
                for unsynced_line in lines1[len(lines2):]:
                    self.process_line(unsynced_line)

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
            self.active_accounts[username] = None
            mutex_active_accounts.release()
        
        # If leader, sync replicas
        if self.is_leader:
            new_text = new_route_guide_pb2.Text()
            new_text.text = username
            for replica in self.backup_connections:
                response = None
                # Block until backups have been successfully updated
                try:
                    response = replica.login_user(new_text)
                except Exception as e:
                    print("Backup is down")
        
        # Write to logs
        text = LOGIN_SUCCESSFUL + SEPARATOR + username
        try:
            logger = logging.getLogger(f'{self.port}')
            logger.info(text)
            for other in self.other_servers:
                other.log_update(new_route_guide_pb2.Note(sender=f'{self.port}', recipient="", message=text))
        except Exception as e:
            print("Error logging to other servers")
        
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
            self.active_accounts[username] = None
            mutex_active_accounts.release()

            mutex_accounts.acquire()
            self.accounts.append(username)
            mutex_accounts.release()

            mutex_unsent_messages.acquire()
            self.unsent_messages[username] = []
            mutex_unsent_messages.release()

            # If leader, sync replicas
            if self.is_leader:
                new_text = new_route_guide_pb2.Text()
                new_text.text = username
                for replica in self.backup_connections:
                    response = None
                    # Block until backups have been successfully updated
                    try:
                        response = replica.register_user(new_text)
                    except Exception as e:
                        print("Backup is down")
            
            # Write to logs
            text = REGISTRATION_SUCCESSFUL + SEPARATOR + username
            try:
                logger = logging.getLogger(f'{self.port}')
                logger.info(text)
                for other in self.other_servers:
                    other.log_update(new_route_guide_pb2.Note(sender=f'{self.port}', recipient="", message=text))
            except Exception as e:
                print("Error logging update")

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

        # Write to logs
        text = UPDATE_SUCCESSFUL + SEPARATOR + recipient
        try:
            logger = logging.getLogger(f'{self.port}')
            logger.info(text)
            for other in self.other_servers:
                other.log_update(new_route_guide_pb2.Note(sender=f'{self.port}', recipient="", message=text))
        except Exception as e:
            print("Error logging update")

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
            for connection in self.backup_connections:
                try:
                    response = connection.replica_client_receive_message(request)
                    if response.text != UPDATE_SUCCESSFUL:
                        print("error with update backup")
                except Exception as e:
                    print("Backup is down")

        return new_route_guide_pb2.Text(text=UPDATE_SUCCESSFUL)
    
    '''Replica handles the clients receiving messages sent to them. Updates the message states of the backups.'''
    def replica_client_receive_message(self, request, context):
        recipient = request.text
        mutex_unsent_messages.acquire()
        self.unsent_messages[recipient] = []
        mutex_unsent_messages.release()
        
        # Write to logs
        text = UPDATE_SUCCESSFUL + SEPARATOR + recipient
        try:
            logger = logging.getLogger(f'{self.port}')
            logger.info(text)
            for other in self.other_servers:
                other.log_update(new_route_guide_pb2.Note(sender=f'{self.port}', recipient="", message=text))
        except Exception as e:
            print("Error logging to other servers")
        
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
        
        # Write to logs
        text = SEND_SUCCESSFUL + SEPARATOR + sender + SEPARATOR + recipient + SEPARATOR + message
        try:
            logger = logging.getLogger(f'{self.port}')
            logger.info(text)
            for other in self.other_servers:
                other.log_update(new_route_guide_pb2.Note(sender=f'{self.port}', recipient="", message=text))
        except Exception as e:
            print("Error logging to other servers")
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
            new_text = new_route_guide_pb2.Text()
            new_text.text = username
            for replica in self.backup_connections:
                response = None
                # Block until backups have been successfully updated
                try:
                    response = replica.delete_account(new_text)
                except Exception as e:
                    print("Backup is down")

        # Write to logs
        text = DELETION_SUCCESSFUL + SEPARATOR + username
        try:
            logger = logging.getLogger(f'{self.port}')
            logger.info(text)
            for other in self.other_servers:
                other.log_update(new_route_guide_pb2.Note(sender=f'{self.port}', recipient="", message=text))
        except Exception as e:
            print("Error logging to other servers")
        
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
            new_text = new_route_guide_pb2.Text()
            new_text.text = username
            for replica in self.backup_connections:
                response = None
                # Block until backups have been successfully updated
                try:
                    response = replica.logout(new_text)
                except Exception as e:
                    print("Backup is down")
        
        # Write to logs
        text = LOGOUT_SUCCESSFUL + SEPARATOR + username
        try:
            logger = logging.getLogger(f'{self.port}')
            logger.info(text)
            for other in self.other_servers:
                other.log_update(new_route_guide_pb2.Note(sender=f'{self.port}', recipient="", message=text))
        except Exception as e:
            print("Error logging to other servers")

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


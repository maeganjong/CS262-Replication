from commands import *
import grpc
import new_route_guide_pb2 as chat
import new_route_guide_pb2_grpc
import atexit

class ChatClient:   
    '''Instantiates the ChatClient and runs the user experience of cycling through chat functionalities.'''
    def __init__(self, test=False):
        if test:
            return 
        
        # TODO: CONSIDER MAKING 3 SERVERs???
        """
        List of ports of replicas in order of priority (for power transfer)
        List will decrease in size as servers go down; first port in list is the leader
        """
        self.replica_ports = [PORT1, PORT2, PORT3]
        self.connection = None

        # Establish connection to first server
        self.find_next_leader()

        atexit.register(self.disconnect)

        self.logged_in = False
        self.username = None

        while not self.logged_in:
            self.login()

        # Receive messages from when they were offline
        self.print_messages()
        
        while self.logged_in:
            self.display_accounts()
            self.print_messages()

            # Try again because recipient invalid
            while self.send_chat_message() == False:
                pass

            self.print_messages()
            
            self.delete_or_logout()
            self.print_messages()
    
    def find_next_leader(self):
        print("Finding next leader...")
        while len(self.replica_ports) > 0:
            current_leader_port = self.replica_ports[0]
            try:
                self.connection = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{SERVER}:{current_leader_port}"))
                response = self.connection.alive_ping(chat.Text(text=IS_ALIVE))
                if response.text == LEADER_ALIVE:
                    # Send message notifying new server that they're the leader
                    confirmation = self.connection.notify_leader(chat.Text(text=LEADER_NOTIFICATION))
                    if confirmation.text == LEADER_CONFIRMATION:
                        print("SWITCHING REPLICAS")
                        # TODO: CHECK IF THERE CAN BE AN ELSE?
                        return
                
                # If for some reason, it gets here (failure), remove current leader from list of ports
                self.replica_ports.pop(0)
            except Exception as e:
                print(e)
                # Remove current leader from list of ports
                self.replica_ports.pop(0)
        
        print("Could not connect to any server (all replicas down).")
        exit()

    '''Disconnect logs out user when process is interrupted.'''
    def disconnect(self):
        # TODO: MIGHT NEED TO CHECK THIS LATER
        print("Disconecting...")
        try:
            response = self.connection.logout(chat.Text(text=self.username))
            print(response.text)
        except Exception as e:
            # Power transfer to a backup replica
            self.find_next_leader()

    '''Logins user by prompting either to register or login to their account.'''
    def login(self):
        logged_in = False
        while not logged_in:
            action = input("Enter 0 to register. Enter 1 to login.\n")
            if action == "0":
                username, logged_in = self.enter_user(action)
                self.logged_in = logged_in
            elif action == "1":
                username, logged_in = self.enter_user(action)
                self.logged_in = logged_in
    
    '''Helper function to login for users to either register or login.'''
    def enter_user(self, purpose):
        # Prompts user for username
        username = input("What's your username?\n")

        new_text = chat.Text()
        new_text.text = username

        response = None
        done = False
        while not done:
            try: 
                if purpose == "0":
                    response = self.connection.register_user(new_text)
                elif purpose == "1":
                    response = self.connection.login_user(new_text)
                
                print(response.text)
                done = True

                if response.text == LOGIN_SUCCESSFUL:
                    self.logged_in = True
                    self.username = username
                    return username, True

            except Exception as e:
                # Power transfer to a backup replica
                self.find_next_leader()

        return username, False

    '''Displays username accounts for the user to preview given prompt.'''
    def display_accounts(self):
        recipient = input("What users would you like to see? Use a regular expression. Enter nothing to skip.\n")
        new_text = chat.Text()
        new_text.text = recipient
        print("\nUsers:")
        done = False
        while not done:
            try:
                accounts = self.connection.display_accounts(new_text)
                for account in accounts:
                    print(account.text)
                done = True
            except Exception as e:
                # Power transfer to a backup replica
                self.find_next_leader()

    
    '''Prompts user to specify recipient of their message and the message body. Creates the Note object encompassing the message then sends the message to the server.'''
    def send_chat_message(self):
        recipient = input("Who do you want to send a message to?\n")
        new_text = chat.Text()
        new_text.text = recipient
        done = False
        while not done:
            try:
                response = self.connection.check_user_exists(new_text)
                if response.text == USER_DOES_NOT_EXIST:
                    print(response.text)
                    return False
                done = True
            except Exception as e:
                # Power transfer to a backup replica
                self.find_next_leader()
        
        message = input("What's your message?\n")
        new_message = chat.Note()
        new_message.sender = self.username
        new_message.recipient = recipient
        new_message.message = message

        done = False
        while not done:
            try:
                output = self.connection.client_send_message(new_message)
                print(output.text)
                done = True
            except Exception as e:
                # Power transfer to a backup replica
                self.find_next_leader()
        
        return True

    '''Handles the print of all the messages sent to the user.'''
    def print_messages(self):
        for message in self.receive_messages():
            print(message)

    '''User pulls message sent to them from the server.'''
    def receive_messages(self):
        done = False
        while not done:
            try:
                notes = self.connection.client_receive_message(chat.Text(text=self.username))
                for note in notes:
                    yield f"[{note.sender} sent to {note.recipient}] {note.message}"
                done = True
            except Exception as e:
                # Power transfer to a backup replica
                # TODO: THIS METHOD DOES NOT WORK!!!! figure out later lmfao
                print(e)
                raise "STOP"
                self.find_next_leader()

    '''Prompts user to delete or logout their account or continue the flow of their chat.'''
    def delete_or_logout(self):
        action = input("Enter 0 to delete your account. Enter 1 to logout. Anything else to continue.\n")
        if action == "0":
            done = False
            while not done:
                try:
                    response = self.connection.delete_account(chat.Text(text=self.username))
                    print(response.text)
                    done = True
                    if response.text == DELETION_SUCCESSFUL:
                        self.logged_in = False
                        self.username = None
                        self.login()
                except Exception as e:
                    # Power transfer to a backup replica
                    self.find_next_leader()
        
        elif action == "1":
            done = False
            while not done:
                try:
                    response = self.connection.logout(chat.Text(text=self.username))
                    print(response.text)
                    done = True
                    if response.text == LOGOUT_SUCCESSFUL:
                        self.logged_in = False
                        self.username = None
                        self.login()
                except Exception as e:
                    # Power transfer to a backup replica
                    self.find_next_leader()
            

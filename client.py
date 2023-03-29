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
        
        self.connection = None
        try:
            self.connection = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{SERVER}:{PORT1}"))
        except Exception as e:
            print(e)
            print("Could not connect to server.")
            return

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

    '''Disconnect logs out user when process is interrupted.'''
    def disconnect(self):
        print("Disconecting...")
        response = self.connection.logout(chat.Text(text=self.username))
        print(response.text)

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
        if purpose == "0":
            try:
                response = self.connection.register_user(new_text)
                print(response.text)
            except Exception as e:
                # TODO: This power transition is hardcoded. Need to make it dynamic.
                print(e)
                self.connection = new_route_guide_pb2_grpc.ChatStub(grpc.insecure_channel(f"{SERVER}:{PORT2}"))
                response = self.connection.register_user(new_text)
                print(response)
        elif purpose == "1":
            response = self.connection.login_user(new_text)
            print(response.text)

        if response.text == LOGIN_SUCCESSFUL:
            self.logged_in = True
            self.username = username
            return username, True
        return username, False

    '''Displays username accounts for the user to preview given prompt.'''
    def display_accounts(self):
        recipient = input("What users would you like to see? Use a regular expression. Enter nothing to skip.\n")
        new_text = chat.Text()
        new_text.text = recipient
        print("\nUsers:")
        for response in self.connection.display_accounts(new_text):
            print(response.text)
    
    '''Prompts user to specify recipient of their message and the message body. Creates the Note object encompassing the message then sends the message to the server.'''
    def send_chat_message(self):
        recipient = input("Who do you want to send a message to?\n")
        new_text = chat.Text()
        new_text.text = recipient
        response = self.connection.check_user_exists(new_text)

        if response.text == USER_DOES_NOT_EXIST:
            print(response.text)
            return False
        
        message = input("What's your message?\n")
        new_message = chat.Note()
        new_message.sender = self.username
        new_message.recipient = recipient
        new_message.message = message

        output = self.connection.client_send_message(new_message)
        print(output.text)
        return True

    '''Handles the print of all the messages sent to the user.'''
    def print_messages(self):
        for message in self.receive_messages():
            print(message)

    '''User pulls message sent to them from the server.'''
    def receive_messages(self):
        for note in self.connection.client_receive_message(chat.Text(text=self.username)):
            yield f"[{note.sender} sent to {note.recipient}] {note.message}"

    '''Prompts user to delete or logout their account or continue the flow of their chat.'''
    def delete_or_logout(self):
        action = input("Enter 0 to delete your account. Enter 1 to logout. Anything else to continue.\n")
        if action == "0":
            response = self.connection.delete_account(chat.Text(text=self.username))
            print(response.text)
            if response.text == DELETION_SUCCESSFUL:
                self.logged_in = False
                self.username = None
                self.login()
        elif action == "1":
            print("output")
            response = self.connection.logout(chat.Text(text=self.username))
            print(response.text)
            if response.text == LOGOUT_SUCCESSFUL:
                self.logged_in = False
                self.username = None
                self.login()

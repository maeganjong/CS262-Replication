# Connection Data
HEADER = 64
PORT1 = 8050
PORT2 = 8051
PORT3 = 8052
FORMAT = 'utf-8'
## Edit Server below to the hostname of the machine running the server
SERVER1 = "dhcp-10-250-116-175.harvard.edu" 
SERVER2 = "dhcp-10-250-116-175.harvard.edu" 
SERVER3 = "dhcp-10-250-116-175.harvard.edu" 

# Data Types
PURPOSE = "!PURPOSE:"
RECIPIENT = "!RECIPIENT:"
SENDER = "!SENDER:"
LENGTH = "!LENGTH:"
BODY = "!BODY:"

# General
SEPARATOR = ": "
MAX_BANDWIDTH = 2048 

# Client Purposes
CHECK_USER_EXISTS = "!CHECKUSEREXISTS"
DELETE_ACCOUNT = "!DELETEACCOUNT"
SHOW_ACCOUNTS = "!SHOWACCOUNTS"
LOGIN = "!LOGIN"
REGISTER = "!REGISTER"
PULL_MESSAGE = "!PULL"
SEND_MESSAGE = "!SEND"

# Server Purposes
NO_MORE_DATA = "!NOMOREDATA"
NOTIFY = "!NOTIFY"

# Printable messages from NOTIFY
LOGIN_SUCCESSFUL = "Login successful!"
REGISTRATION_SUCCESSFUL = "Registration successful!"
USER_DOES_NOT_EXIST = "User does not exist."
DELETION_SUCCESSFUL = "Account deleted."
DELETION_UNSUCCESSFUL = "Account cannot be deleted."
LOGOUT_SUCCESSFUL = "Logout successful."
UPDATE_SUCCESSFUL = "Update successful."
SEND_SUCCESSFUL = "Message sent!"

# Power transfer purposes
LEADER_ALIVE = "Leader is alive."
IS_ALIVE = "Are you alive?"
LEADER_NOTIFICATION = "Leader notification." # Notifies backup that they are now leader
LEADER_CONFIRMATION = "Leader confirmation." # Notifies client that backup is now leader

# Other
DISCONNECT_MESSAGE = "!DISCONNECT"
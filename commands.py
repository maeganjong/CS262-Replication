# Connection Data
HEADER = 64
PORT1 = 8500
PORT2 = 8501
PORT3 = 8502
FORMAT = 'utf-8'
## Edit Server below to the hostname of the machine running the server
SERVER = "dhcp-10-250-116-175.harvard.edu" 

# Data Types
PURPOSE = "!PURPOSE:"
RECIPIENT = "!RECIPIENT:"
SENDER = "!SENDER:"
LENGTH = "!LENGTH:"
BODY = "!BODY:"

# General
SEPARATOR = "/"
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
USER_DOES_NOT_EXIST = "User does not exist."
DELETION_SUCCESSFUL = "Account deleted."
DELETION_UNSUCCESSFUL = "Account cannot be deleted."
LOGOUT_SUCCESSFUL = "Logout successful."

# IDK WHERE THIS ONE IS YET
DISCONNECT_MESSAGE = "!DISCONNECT"
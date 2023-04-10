from server import *

# Chat server for persistence. Run after all other chat servers are down.
logname = "8052.log"
chat_server = ServerRunner(ip=SERVER1, port=PORT1, logfile = logname) # NOTE THESE CANNOT BE THE SAME!
print("[STARTING] lead server is starting...")
chat_server.start()

chat_server.connect_to_replicas((SERVER2, PORT2), (SERVER3, PORT3))

chat_server.wait_for_termination()
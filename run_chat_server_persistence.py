from server import *

# Chat server for persistence. Run after all other chat servers are down.
logname = "persistence_demo.log"
chat_server = ServerRunner(ip=SERVER1, port=PORT1, logfile = logname) # NOTE THESE CANNOT BE THE SAME!
print("[STARTING] lead server is starting...")
chat_server.start()

chat_server.wait_for_termination()
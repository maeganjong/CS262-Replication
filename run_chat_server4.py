from server import *

# Chat server for persistence. Run after all other chat servers are down.
# TODO: THIS IS A TESTER
chat_server = ServerRunner(port=PORT1, logfile = "8052.log") # NOTE THESE CANNOT BE THE SAME!
print("[STARTING] lead server is starting...")
chat_server.start()

chat_server.connect_to_replicas(PORT2, PORT3)

chat_server.wait_for_termination()
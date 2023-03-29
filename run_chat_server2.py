from server import *

chat_server = ServerRunner(port=PORT2)
print("[STARTING] backup 1 is starting...")
chat_server.start()

chat_server.connect_to_replicas(PORT1, PORT3)
print("Connected to replicas")

chat_server.wait_for_termination()
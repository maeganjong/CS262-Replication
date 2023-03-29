from server import *

chat_server = ServerRunner(port=PORT1)
print("[STARTING] lead server is starting...")
chat_server.start()

chat_server.connect_to_replicas(PORT2, PORT3)
print("Connected to replicas")

chat_server.wait_for_termination()
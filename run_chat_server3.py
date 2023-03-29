from server import *

chat_server = ServerRunner(port=PORT3)
print("[STARTING] backup 2 is starting...")
chat_server.start()

chat_server.connect_to_replicas(PORT1, PORT2)
print("Connected to replicas")

chat_server.wait_for_termination()

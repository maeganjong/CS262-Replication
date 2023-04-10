from server import *

chat_server = ServerRunner(ip=SERVER3, port=PORT3)
print("[STARTING] backup 2 is starting...")
chat_server.start()

chat_server.connect_to_replicas((SERVER1, PORT1), (SERVER2, PORT2))

chat_server.wait_for_termination()

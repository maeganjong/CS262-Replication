from server import *

chat_server = ServerRunner(ip=SERVER2, port=PORT2)
print("[STARTING] backup 1 is starting...")
chat_server.start()

chat_server.connect_to_replicas((SERVER1, PORT1), (SERVER3, PORT3))

chat_server.wait_for_termination()
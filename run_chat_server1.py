from server import *

chat_server = ServerRunner(ip=SERVER1, port=PORT1)
print("[STARTING] lead server is starting...")
chat_server.start()

chat_server.connect_to_replicas((SERVER2, PORT2), (SERVER3, PORT3))

chat_server.wait_for_termination()
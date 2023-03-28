from server import *

# TODO: THIS IS BAD CODE BUT FIX LATER
chat_server1 = ServerRunner(port=8050)
print("[STARTING] server 1 is starting...")
chat_server1.start()

chat_server2 = ServerRunner(port=8051)
print("[STARTING] server 2 is starting...")
chat_server2.start()

chat_server3 = ServerRunner(port=8052)
print("[STARTING] server 3 is starting...")
chat_server3.start()

chat_server1.connect_to_replicas(8051, 8052)
chat_server2.connect_to_replicas(8050, 8052)
chat_server3.connect_to_replicas(8051, 8050)
print("DONE")

chat_server1.wait_for_termination()
chat_server2.wait_for_termination()
chat_server3.wait_for_termination()
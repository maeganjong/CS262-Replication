# CS262 Replication

Engineering Ledger: https://docs.google.com/document/d/11WlBTULYnyn-tCe7IGBXiVid2h6U9yl1P-U38izuWwk/edit?usp=sharing

## Running the Code

### Setup
1. Setup a new environment through `spec-file.txt`. Run `conda create --name <env> --file spec-file.txt`
2. Run `conda activate <env>`.
3. Change the server address `SERVER1`, `SERVER2`, `SERVER3` values in `commands.py` to the `hostname` of your servers. To find hostname, enter `hostname` on your terminal.

### Running the Servers
1. Open a new terminal session for each server.
2. Run `python3 run_chat_server{n}.py` such that `{n}` is the server number. For example, for server 1, run `python3 run_chat_server1.py`.

### Running the Clients
1. Open a new terminal session for each client.
2. Run `python3 run_chat_client.py`.
3. Follow the prompts provided to send and receive messages. You can initialize as many client sessions as you'd like on different machines.

### Persistence Server
In the situation that all three servers are down, a new server can be brought up with the last state, including any unsent messages. 
1. To customize the log file you reference for the last state, change the `logname` variable. Note, `logname` cannot have the same number and filename as the `port` that the server is connecting with since the server cannot reference a log that it's trying to write to at the same time.
1. Open a new terminal session for the server.
2. Run `python3 run_chat_server_persistence.py`.

## Understanding Log Files
- Each log file is named according to the port number of the server writing to that file.
- Log files capture all major actions of the chat messaging service.
- Log files can be used to provide persistence of the system.

## Running Tests
1. To run server tests, run `pytest server_tests.py`
2. To run process tests, run `pytest process_tests.py`

import socket

HOST = 'shots-alarm'  # The server's hostname or IP address
PORT = 8675        # The port used by the server

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.send(b'ACTIVATE')

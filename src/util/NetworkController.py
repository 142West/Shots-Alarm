import socket

from src import Private


class NetworkController:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('', int(Private.REMOTE_PORT)))
        self.status = "Waiting"
        self.conn = None
        self.addr = None

    async def getData(self):
        if self.addr:
            while True:
                data = self.conn.recv(1024)
                if data.decode() == "ACTIVATE":
                    self.conn.sendall(b"ACK")
                    return "ACTIVATE"
                if data.decode() == "ABORT":
                    self.conn.sendall(b"ACK")
                    return "ABORT"
                if not data:
                    break
        else:
            return None

    def connect(self):
        self.s.listen()
        self.conn, self.addr = self.s.accept()
        self.status = "Connected"

    def getStatus(self):
        return self.status, 0

    def close(self):
        if self.conn:
            self.conn.close()
        #self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()

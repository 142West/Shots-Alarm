import socket


class ShotsNetworkController:
    def __init__(self, remotePort, logger):
        self.logger = logger
        try:
            self.status = "Waiting"
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind(('0.0.0.0', int(remotePort)))
        except OSError as e:
            logger.critical(e)

        self.conn = None
        self.addr = None

    def getData(self):
        self.logger.debug(f"Getting data... {self.addr}")
        if self.addr:
            while True:
                data = self.conn.recv(1024)
                self.logger.debug(f"Got data: {data} ({data.decode()})")
                if data.decode().strip() == "ACTIVATE":
                    self.conn.sendall(b"ACK")
                    return "ACTIVATE"
                if data.decode().strip() == "ABORT":
                    self.conn.sendall(b"ACK")
                    return "ABORT"
                if not data:
                    break
        else:
            return None

    def connect(self):
        self.logger.debug("Listening")
        self.s.listen()

        self.conn, self.addr = self.s.accept()
        self.status = "Connected"

    def getStatus(self):
        return self.status, 0

    def close(self):
        self.logger.debug("Shutting Down")
        if self.conn:
            self.conn.close()
        #self.s.shutdown(socket.SHUT_RDWR)
        self.s.close()

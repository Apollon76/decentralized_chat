import queue

from src import utils
from src import packet


class Reader(utils.Daemon):
    def __init__(self, connection, packet_size: int):
        super().__init__(name='reading', target=self._read)
        self.connection = connection
        self._buffer = bytearray()
        self.packet_size = packet_size
        self.messages = queue.Queue()

    def _read(self):
        self._buffer.extend(self.connection.recv(self.packet_size))
        self._flush()

    def _flush(self):
        while True:
            try:
                size = packet.Packet.get_data_size(self._buffer)
            except ValueError:
                return
            packets = self._buffer.decode()
            if len(self._buffer.decode()) < 1 + 8 + 8 + size:
                return
            self.messages.put(bytes(packets[:1 + 8 + 8 + size], 'utf-8'))
            self._buffer = bytearray(packets[1 + 8 + 8 + size:], 'utf-8')

    def get(self):
        if not self.messages.empty():
            return self.messages.get()

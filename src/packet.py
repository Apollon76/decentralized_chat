import enum
import random


class PacketType(enum.Enum):
    CONNECTION = 'c'
    CONFIRMATION = 'y'
    GET_IP = 'g'
    IP = 'z'
    LOGIN = 'n'
    LOGOUT = 'o'
    MESSAGE = 's'
    ONLINE = 'l'
    DATA = ''


class Packet:
    def __init__(self, t: PacketType, data='', msg_id=None):
        self.type = t
        if msg_id is None:
            msg_id = random.randint(0, 2 ** 64 - 1)
        self._id = msg_id
        self._size = len(data)
        self.data = data

    @staticmethod
    def to_bytes(x: int) -> str:
        s = ''
        for i in range(8):
            s += chr(x % 255 + 1)
            x //= 255
        return s

    @staticmethod
    def to_int(s: str) -> int:
        if len(s) != 8:
            raise ValueError('Incorrect length of string')
        x = 0
        for i in range(8):
            x += (ord(s[i]) - 1) * (255 ** i)
        return x

    @staticmethod
    def get_data_size(s: bytearray) -> int:
        s = s.decode()
        if len(s) < 1 + 8 + 8:
            raise ValueError('Too short sequence')
        return Packet.to_int(s[9:17])

    @property
    def id(self):
        return self._id

    @id.setter
    def id(self, x):
        if not 0 <= x < 2 ** 60:
            raise ValueError('ID must satisfy this statement: 0 <= ID < 2 ** 60')
        self._id = x

    def __bytes__(self):
        return bytes(self.type.value + (self.to_bytes(self.id) if self.id is not None else '') + self.to_bytes(self._size) + self.data, 'utf-8')

    def __repr__(self):
        return '{} : {} : {}'.format(self.type, str(self.id), self.data)

    def __str__(self):
        return self.data

    @staticmethod
    def parse(byte_string):
        types = dict(map(lambda x: (x.value, x), PacketType))
        byte_string = byte_string.decode()
        t = byte_string[0]
        t = types[t]
        msg_id = Packet.to_int(byte_string[1:9])
        size = Packet.to_int(byte_string[9:17])
        data = byte_string[17:17 + size]
        return Packet(t, data, msg_id)

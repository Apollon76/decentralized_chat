import threading
import time

from src import utils
from src import server
from src import log
from src.packet import Packet, PacketType
from src.message import Message, MessageType


class Client:
    def __init__(self, nickname: str, chat_addr=None, server_port=None):
        self.online_updater = utils.Daemon(name='online', target=self.online, timeout=10)
        self._server = server.Server(chat_addr, server_port)
        self.nickname = nickname
        self._logger = log.Log('../log.txt')
        self.users_list_lock = threading.RLock()
        self.black_list = utils.SafeSet()
        # TODO make it safe
        self.users_list = {}
        self.users_list_refresher = utils.Daemon(name='users_list_refresher', target=self.refresh, timeout=5)

    def run(self):
        self.online_updater.run()
        self.users_list_refresher.run()
        self._server.run()

    def get(self) -> Message:
        if self._server.got_messages.empty():
            return
        message = self._server.got_messages.get()
        self._logger.get(message)
        if message.type is PacketType.ONLINE:
            with self.users_list_lock:
                self.users_list[message.data] = time.monotonic()
            return None
        message = Message.parse(message.data)
        if message.nickname in self.black_list:
            return None
        if message.type is MessageType.PRIVATE and \
                message.addressee != self.nickname and message.nickname != self.nickname:
            return None
        return message

    def send_message(self, message: Message):
        message.nickname = self.nickname
        message = Packet(PacketType.MESSAGE, repr(message))
        self._server.got_messages.put(message)
        self.send(message)

    def send(self, message: Packet):
        self._server.received.add(message.id)
        self._server.send(message)

    def online(self):
        message = Packet(PacketType.ONLINE, self.nickname)
        self.send(message)

    def refresh(self):
        cur_time = time.monotonic()
        with self.users_list_lock:
            self.users_list = dict(filter(lambda user: cur_time - user[1] < 30, self.users_list.items()))

    def close(self):
        self.online_updater.stop()
        self.users_list_refresher.stop()
        self._server.close()

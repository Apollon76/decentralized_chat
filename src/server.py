import copy
import queue
import random
import threading
import socket
import time

from src.packet import Packet, PacketType
from src import reader
from src import utils


class Server:
    def __init__(self, chat_addr=None, server_port=None):
        self.sending_message_queue = queue.Queue()
        self.got_messages = queue.Queue()
        self._server_host = ''
        self._server_port = server_port
        self._receive_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._receive_socket.bind((self._server_host, self._server_port))
        self._receive_socket.listen(1024)
        self._readers = []
        self._connections = []
        self.packet_size = 4096
        self._sent = utils.SafeSet()
        self.received = utils.SafeSet()
        self.lock = threading.Lock()
        self._sending = utils.Daemon(name='sending', target=self._send_to_clients, timeout=0)
        self._getting = utils.Daemon(name='getting', target=self.get)
        self._accepting = utils.Daemon(name='accepting', target=self._accept, timeout=1)
        self._connection_event = threading.Event()
        self.ip_list = utils.SafeSet()
        self._question_id = None
        self._par_conn = None
        with self.lock:
            if chat_addr is not None:
                self._connect(chat_addr[0], chat_addr[1])

    def run(self):
        with self.lock:
            self._sending.run()
            self._getting.run()
            self._accepting.run()

    def send(self, message: Packet):
        if message.id is None:
            message.id = random.randint(0, 2 ** 60 - 1)
        if message.id in self._sent:
            return
        self._sent.add(message.id)
        self.sending_message_queue.put(message)
        self._sending.run()

    def _connect(self, chat_host, chat_port: int):
        connection = socket.socket()
        connection.connect((chat_host, chat_port))
        connection.send(bytes(Packet(PacketType.CONNECTION)))
        info = b''
        while len(info) == 0:
            time.sleep(1)  # TODO
            info = connection.recv(self.packet_size)
        info = Packet.parse(info)
        if info.type is PacketType.CONFIRMATION:
            self._connections.append(connection)
            connection.send(bytes(Packet(PacketType.CONFIRMATION, str(self._server_port))))
            self._par_conn = connection
            print('connected')
            new_reader = reader.Reader(connection, self.packet_size)
            self._readers.append(new_reader)
            new_reader.run()
            self.ip_list.add(chat_host + ':' + str(chat_port))
            time.sleep(1)  # TODO
            question = Packet(PacketType.GET_IP)
            self.send(question)
            self.received.add(question.id)
            self._question_id = question.id

    def _accept(self):
        conn = None
        try:
            conn, addr = self._receive_socket.accept()
            print(addr)
            with self.lock:
                info = Packet.parse(conn.recv(self.packet_size))
                if info.type is PacketType.CONNECTION:
                    conn.send(bytes(Packet(PacketType.CONFIRMATION)))
                    time.sleep(2)  # TODO
                    info = Packet.parse(conn.recv(self.packet_size))
                    if info.type is PacketType.CONFIRMATION:
                        self._connections.append(conn)
                        new_reader = reader.Reader(conn, self.packet_size)
                        self._readers.append(new_reader)
                        new_reader.run()
                        self.ip_list.add(addr[0] + ':' + info.data)
                        self.send(Packet(PacketType.IP, '/' + addr[0] + ':' + info.data))
                        print('accepted')
        except OSError:
            if conn is not None:
                conn.close()

    def _send_to_clients(self):
        if self.sending_message_queue.empty():
            self._sending.stop()
            return
        current_message = self.sending_message_queue.get()
        bad_connections = []
        connections = copy.copy(self._connections)
        for connection in connections:
            try:
                connection.sendall(bytes(current_message))
            except BrokenPipeError or ConnectionResetError:
                self._connection_event.clear()
                if connection is self._par_conn:
                    self._repair_net()
                    # self._par_conn.sendall(bytes(current_message))
                bad_connections.append(connection)
        for connection in bad_connections:
            self._connections.remove(connection)

    def get(self):
        with self.lock:
            for reader in self._readers:
                data = reader.get()
                if data is not None:
                    self._process(data)

    def _process(self, data: bytes):
        message = Packet.parse(data)
        if message.id in self.received:
            return
        self.received.add(message.id)
        if message.type is PacketType.MESSAGE or message.type is PacketType.ONLINE:
            self.got_messages.put(message)
            self.send(message)
        if message.type is PacketType.IP:
            cur_id, addr = message.data.split('/')
            self.ip_list.add(addr)
            self.send(message)
        if message.type is PacketType.GET_IP:
            self.send(message)
            for ip in self.ip_list:
                self.send(Packet(PacketType.IP, '{}/{}'.format(message.data, ip)))
        # print(self.ip_list)

    def _repair_net(self):
        for addr in self.ip_list:
            addr = addr.split(':')
            try:
                self._connect(addr[0], int(addr[1]))
                break
            except ConnectionError:
                pass

    def close(self):
        self._sending.stop()
        self._getting.stop()
        self._accepting.stop()
        self._receive_socket.shutdown(2)
        self._receive_socket.close()
        for r in self._readers:
            r.stop()
        for connection in self._connections:
            connection.shutdown(socket.SHUT_RDWR)
            connection.close()

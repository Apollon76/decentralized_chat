from tkinter import *

from tkinter.scrolledtext import ScrolledText

from src.client import Client
from src import utils
from src.message import Message, MessageType


class InputBox(Text):
    def __init__(self, frame, height, width, font, func):
        super().__init__(frame, height=height, width=width, font=font)
        self.bind('<KeyRelease-Return>', func)
        # self.bind('<Key>', self._remove_empty_string)

    def _remove_empty_strings(self, _):
        if self.get('0.0', END) == '\n':
            self.delete('0.0', END)


class MessagesList(ScrolledText):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind_all('<<Copy>>', self.copy_text)

    def copy_text(self, _=None):
        selected = self.selection_get()
        self.clipboard_clear()
        self.clipboard_append(selected)


class UserWindow(Tk):
    def __init__(self, nickname: str, client: Client):
        super().__init__()
        self.title(nickname)
        self.client = client
        self.nickname = nickname
        self.input_box = InputBox(self, height=3, width=30,
                                  font=('Times New Roman', 11), func=self._send_private_message)
        self.input_box.pack()
        self.private_message_button = Button(self, text='Приватное сообщение',
                                             width=len('Приватное сообщение') + 2,
                                             command=self._send_private_message)
        self.private_message_button.pack()
        self.move_to_black_list_button = Button(self, text='В игнор',
                                                width=len('В игнор') + 2,
                                                command=self._move_to_black_list)
        self.move_from_black_list_button = Button(self, text='Из игнора',
                                                  width=len('Из игнора') + 2,
                                                  command=self._move_from_black_list)
        if self.nickname not in self.client.black_list:
            self.move_to_black_list_button.pack()
        else:
            self.move_from_black_list_button.pack()

    def _move_to_black_list(self):
        self.client.black_list.add(self.nickname)
        self.move_to_black_list_button.pack_forget()
        self.move_from_black_list_button.pack()

    def _move_from_black_list(self):
        self.client.black_list.remove(self.nickname)
        self.move_from_black_list_button.pack()
        self.move_to_black_list_button.pack_forget()

    def _send_private_message(self, _=None):
        message = self.input_box.get('0.0', END)
        # TODO encapsulate
        self.input_box.delete('0.0', END)
        message = message.rstrip(u'\n')
        if message == '':
            return
        message = Message(MessageType.PRIVATE, message)
        message.addressee = self.nickname
        self.client.send_message(message)

    def show(self):
        self.mainloop()


class UserList(utils.VerticalScrolledFrame):
    def __init__(self, root, client: Client, width=30):
        super().__init__(root, width=width)
        self._client = client
        self._refresher = utils.Daemon('gui_user_list_refresher', target=self.refresh, timeout=2)
        self.buttons = []

    def run(self):
        self._refresher.run()

    def refresh(self):
        for i in self.buttons:
            i.destroy()
        self.buttons.clear()
        users = sorted(list(self._client.users_list.keys()))

        def make_cmd(x):
            return lambda: self._open_profile(x)

        for user in users:
            cur = Button(self.interior, text=user, width=len(user) + 2, command=make_cmd(user))
            cur.pack(fill=X)
            self.buttons.append(cur)

    def _open_profile(self, nickname: str):
        user_window = UserWindow(nickname, self._client)
        user_window.show()

    def close(self):
        self._refresher.stop()


class NicknameBar(Tk):
    def __init__(self):
        super().__init__()
        self.title('Чат')
        text = Label(self, text='Введите ник: ')
        text.focus_set()
        text.grid(row=0)
        entry_field = Entry(self)
        self.nick = ''

        def destroy(_):
            nonlocal entry_field
            self.nick = entry_field.get()
            if not self.nick or len(self.nick) > 30:
                return
            self.destroy()
            self.quit()

        entry_field.bind('<Return>', destroy)
        entry_field.grid(row=0, column=1)

    def get(self) -> str:
        self.mainloop()
        if not self.nick:
            raise GeneratorExit()
        return self.nick


class Interface:
    def __init__(self, chat_addr=None, server_port=None):
        if chat_addr is None and server_port is None:
            server_port, chat_addr = self.get_port_and_ip()
        self.buttons = []
        self.root = None
        self.main_frame = None
        self.messages_box = None
        self.message_input_box = None
        self.client = None
        self.refresher = utils.Daemon(name='refreshing', target=self.refresh, timeout=0.1)
        self.users_list = None
        if server_port is None:
            self.close()
            return
        nickname = self.get_nickname()
        self.client = Client(nickname, chat_addr, server_port)

    @staticmethod
    def get_port_and_ip():
        root = Tk()
        root.title('Чат')
        port, ip = None, None

        def create_new():
            nonlocal port, ip, root, server_port_field
            try:
                port = int(server_port_field.get())
            except ValueError:
                return
            ip = None
            root.destroy()

        def connect():
            nonlocal root, port, ip
            try:
                port = int(server_port_field.get())
            except ValueError:
                return
            try:
                ip = chat_ip_field.get(), int(chat_port_field.get())
            except ValueError:
                return
            root.destroy()

        server_port_label = Label(root, text='Введите порт: ')
        server_port_label.focus_set()
        server_port_label.pack()
        server_port_field = Entry(root)
        server_port_field.insert(END, '9090')
        server_port_field.pack()

        button_create_new = Button(root, text='Создать', width=len('Создать') + 2, command=create_new)
        button_create_new.pack()
        button_create_new.pack_propagate(False)

        ip_label = Label(root, text='Введите IP: ')
        ip_label.focus_set()
        ip_label.pack()
        chat_ip_field = Entry(root)
        chat_ip_field.pack()

        port_label = Label(root, text='Введите порт подключения: ')
        port_label.pack()
        chat_port_field = Entry(root)
        chat_port_field.pack()

        button_connect = Button(root, text='Подключиться', width=len('Подключиться') + 2, command=connect)
        button_connect.pack()
        button_connect.pack_propagate(False)
        root.mainloop()
        return port, ip

    def init_UI(self):
        self.root = Tk()
        self.root.title('Чат')
        self.root.minsize(width=700, height=300)
        menu = Menu(self.root)
        self.root.config(menu=menu)
        settings = Menu(menu)
        menu.add_cascade(label='Настройки', menu=settings)
        settings.add_command(label='Сменить ник', command=self.change_nickname)
        self.users_list = UserList(self.root, self.client, width=200)
        self.users_list.pack(fill=Y, side=LEFT, anchor=SW)
        self.users_list.pack_propagate(0)
        self.main_frame = Frame(self.root, width=600, height=300)
        self.main_frame.pack(fill=BOTH, expand=1, side=LEFT, anchor=SW)
        self.root.protocol('WM_DELETE_WINDOW', self.close)

        self.messages_box = MessagesList(self.main_frame, height=7, width=30, font=('Times New Roman', 11))
        self.messages_box.config(state=DISABLED)
        self.messages_box.pack(fill=BOTH, expand=1)

        self.message_input_box = InputBox(self.main_frame, height=3, width=30,
                                          font=('Times New Roman', 11), func=self.send)
        self.message_input_box.pack(fill=BOTH, expand=1)
        self.message_input_box.focus_set()
        self.make_button('Отправить', 0, 2, self.send)

    def make_button(self, text: str, x: int, y: int, command):
        button = Button(self.main_frame, text=text, width=len(text) + 2, command=command)
        button.pack()
        button.pack_propagate(False)
        self.buttons.append(button)
        return button

    def get_nickname(self) -> str:
        try:
            return NicknameBar().get()
        except GeneratorExit:
            if self.client is None or not self.client.nickname:
                self.close()

    def change_nickname(self, _=None):
        nickname = self.get_nickname()
        self.client.send_message(Message(MessageType.SHARED, 'Сменил ник на ' + nickname))
        self.client.nickname = nickname  # TODO critical section

    def send(self, _=None):
        beginning = '0.0'
        message = self.message_input_box.get(beginning, END)
        # TODO encapsulate
        self.message_input_box.delete(beginning, END)
        message = message.rstrip(u'\n')
        if message == '':
            return
        message = Message(MessageType.SHARED, message)
        self.client.send_message(message)

    def run(self):
        self.init_UI()
        self.client.run()
        self.refresher.run()
        self.users_list.run()
        self.root.mainloop()

    def refresh(self):
        message = self.client.get()
        if message is not None:
            self.get_message(message)

    def get_message(self, message: Message):
        nickname_start, nickname_end = message.get_nick_position()
        message = str(message) + '\n'
        self.messages_box.config(state=NORMAL)
        need_to_scroll = False
        if self.messages_box.yview()[1] > 0.9:
            need_to_scroll = True
        cur_line, cur_column = map(int, self.messages_box.index(END).split('.'))
        cur_line -= 1
        self.messages_box.insert(END, message)
        self.messages_box.tag_add('nickname', '{}.{}'.format(cur_line, nickname_start),
                                  '{}.{}'.format(cur_line, nickname_end))
        self.messages_box.tag_config('nickname', foreground='blue')
        self.messages_box.config(state=DISABLED)
        if need_to_scroll:
            self.messages_box.see(END)

    def close(self):
        self.refresher.stop()
        if self.users_list is not None:
            self.users_list.close()
        if self.root is not None:
            self.root.destroy()
            self.root.quit()
        if self.client is not None:
            self.client.close()
        sys.exit(0)

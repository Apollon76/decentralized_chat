import enum


class MessageType(enum.Enum):
    SHARED = 's'
    PRIVATE = 'p'


class Message:
    def __init__(self, type: MessageType, source: str):
        self.type = type
        self.source = source
        self.nickname = ''
        self.addressee = ''

    def get_nick_position(self):
        if self.type is MessageType.SHARED:
            return 0, len(self.nickname)
        elif self.type is MessageType.PRIVATE:
            return len('(Приватно) '), len('(Приватно) ') + len(self.nickname)

    def __str__(self):
        if self.type is MessageType.SHARED:
            return '{}: {}'.format(self.nickname, self.source)
        elif self.type is MessageType.PRIVATE:
            return '(Приватно) {}: {}'.format(self.nickname, self.source)

    def __repr__(self):
        if self.type is MessageType.SHARED:
            return '{}:{}:{}'.format(self.type.value, self.nickname, self.source)
        elif self.type is MessageType.PRIVATE:
            return '{}:{}:{}:{}'.format(self.type.value, self.addressee, self.nickname, self.source)

    @staticmethod
    def parse(source: str):
        types = dict(map(lambda x: (x.value, x), MessageType))
        parsed = source.split(':')
        try:
            t = types[parsed[0]]
        except KeyError:
            raise ValueError('Unknown type of message: ' + parsed[0], source)
        ind = 1
        addressee = None
        if t is MessageType.PRIVATE:
            addressee = parsed[ind]
            ind += 1
        nickname = parsed[ind]
        ind += 1
        text = ':'.join(parsed[ind:])
        message = Message(t, text)
        message.nickname = nickname
        message.addressee = addressee
        return message

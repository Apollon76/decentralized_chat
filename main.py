from src import gui


def main():
    '''
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', nargs=1, help='Port on your computer', type=int)
    parser.add_argument('--chat_ip', nargs=2, help='Another user host and port', type=str)
    args = parser.parse_args()
    chat_port = 9090
    if args.port is not None:
        chat_port = args.port[0]
    addr = None
    if args.chat_ip is not None:
        host = args.chat_ip[0]
        port = int(args.chat_ip[1])
        addr = (host, port)
    # app = gui.Interface(addr, chat_port)
    '''
    app = gui.Interface()
    app.run()


if __name__ == '__main__':
    main()

import socket
import queue
import threading


class TcpClient:
    # __TCP_IP = '127.0.0.1'
    __TCP_IP = ''
    __TCP_PORT = 5007
    __BUFFER_SIZE = 64
    
    def __init__(self) -> None:
        self.connection_active = False

        self.__messages = queue.Queue()
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__stop_thread = threading.Thread(name="Stop Thread",
                                              target=self.__wait_for_stop)
        self.__send_thread = threading.Thread(name="Send Thread",
                                              target=self.__send)

    def connect(self):
        print('TcpClient: Try to connect')
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.__socket.bind((self.__TCP_IP, self.__TCP_PORT))
        self.__socket.listen(1)
        self.__conn, self.__addr = self.__socket.accept()
        print('TcpClient: Connection accepted')

        self.__wait_for_start()

    def run(self):
        self.__stop_thread = threading.Thread(name="Stop Thread",
                                              target=self.__wait_for_stop)
        self.__send_thread = threading.Thread(name="Send Thread",
                                              target=self.__send)
        self.__stop_thread.start()
        self.__send_thread.start()

        self.__stop_thread.join()
        print('TcpClient: Stop thread is done')

        self.__send_thread.join()
        print('TcpClient: Send thread is done')

        self.__conn.close()
        self.__socket.close()
    
    def put_message(self, msg):
        self.__messages.put(msg)

    def stop(self):
        self.__conn.close()
        self.__socket.close()

    def __wait_for_start(self):
        self.__wait_for(b'start')
        print('TcpClient: Start detected')
        self.connection_active = True
    
    def __wait_for_stop(self):
        self.__wait_for(b'stop')
        print('TcpClient: Stop detected')
        self.connection_active = False

    def __wait_for(self, message: bytes):
        while True:
            data = self.__conn.recv(self.__BUFFER_SIZE)
            if data == message:
                break

    def __send(self):
        while self.connection_active:
            if not self.__messages.empty():
                message = self.__messages.get()
                self.__conn.send(message)

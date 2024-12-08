import socket
import threading
import sqlite3
import pickle
import traceback
import os

from Peer_to_peer_communication import *
from Support import *
from Metadata_torent import *

HOST_NAME = socket.gethostname()
HOST_IP = socket.gethostbyname(HOST_NAME)
PORT = 1607

class TorrentTracker:
    def __init__(self, db_file='torrent_tracker.db'):
        self.conn = sqlite3.connect(db_file, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.lock = threading.Lock()

        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.bind((HOST_IP, PORT))
        self.server_socket.listen(5)
        self._initialize_database()

        self.tracked_files = set()
        self.file_peers = {}

    def _initialize_database(self):
        with self.lock:
            self.cursor.execute('''CREATE TABLE IF NOT EXISTS clients (
                                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                                    username TEXT UNIQUE,
                                    password TEXT,
                                    ip TEXT,
                                    port INTEGER,
                                    status INTEGER
                                    )''')
            self.conn.commit()
            self.cursor.execute("DELETE FROM clients")
            self.cursor.execute("UPDATE sqlite_sequence SET seq = 0 WHERE name = 'clients'")
            self.conn.commit()

    def handle_peer_connection(self, client_socket, client_address):
       
        print(f"Handling connection from {client_address}")
        while True:
            try:
                data = receive_message(client_socket)
                if data is None:
                    print(f"Connection closed by {client_address}")
                    break
                print(f"Received data from {client_address}")
            
                peer_message = pickle.loads(data)

            # Kiểm tra xem peer_message có phải là dictionary không
                if not isinstance(peer_message, dict):
                    raise ValueError("Received data is not a valid message dictionary")
                required_keys = ['username', 'password', 'ip', 'port', 'type']
                missing_keys = [key for key in required_keys if key not in peer_message]
                if missing_keys:
                    raise ValueError(f"Missing keys in message: {', '.join(missing_keys)}")

                self._process_peer_request(client_socket, peer_message)

            except Exception as e:
                print(f"Error during communication with {client_address}: {e}")
                traceback.print_exc()
                break
        client_socket.close()

    def _process_peer_request(self, client_socket, message):
        message_type = message.get('type')
        if message_type == REGISTER:
            self.register_peer(client_socket, message)
        elif message_type == LOGIN:
            self.login_peer(client_socket, message)
        elif message_type == UPLOAD_FILE:
            self.upload_file(client_socket, message)
        elif message_type == REQUEST_FILE:
            self.handle_file_request(client_socket, message['file_name'])
        elif message_type == GET_LIST_FILES_TO_DOWNLOAD:
            self.send_file_list(client_socket)
        elif message_type == LOGOUT:
            self.logout_peer(client_socket, message)

    def register_peer(self, client_socket, message):
    # Kiểm tra các trường cần thiết có trong message hay không
        required_fields = ['username', 'password', 'ip', 'port']
        for field in required_fields:
            if field not in message:
                self.send_response(client_socket, REGISTER_FAILED, f"Missing field: {field}")
                return

        username = message['username']
        password = message['password']
        ip = message['ip']
        port = message['port']

        print(f"Registering {username}")
        try:
        # Kiểm tra nếu tài khoản đã tồn tại trong cơ sở dữ liệu
            if self.get_client(username):
                self.send_response(client_socket, REGISTER_FAILED, "Account already exists")
            else:
            # Thêm client mới vào cơ sở dữ liệu
                self.add_new_client(username, password, ip, port)
                peer_id = self.get_client_id(username)
                self.send_response(client_socket, REGISTER_SUCCESSFUL, peer_id)
        except Exception as e:
            print(f"Error during registration: {e}")
            traceback.print_exc()
            self.send_response(client_socket, REGISTER_FAILED, "Server error")



    def login_peer(self, client_socket, message):
        username, password, ip, port = message['username'], message['password'], message['ip'], message['port']
        print(f"User {username} logging in")
        try:
            client = self.get_client(username)
            if client and client[2] == password:
                peer_id = self.get_client_id(username)
                self.update_client_status(username, ip, port)
                self.send_response(client_socket, LOGIN_SUCCESSFUL, peer_id)
            else:
                self.send_response(client_socket, LOGIN_FAILED, "Incorrect password")
        except Exception as e:
            print(f"Error during login: {e}")
            traceback.print_exc()
            self.send_response(client_socket, LOGIN_FAILED, "Server error")

    def upload_file(self, client_socket, message):
        file_meta = message['file_meta']
        print(f"Uploading file: {file_meta['file_name']}")
        self.tracked_files.add(file_meta['file_name'])
        file_name = file_meta['file_name']
        if file_name not in self.file_peers:
            self.file_peers[file_name] = set()

        peer_id = message['peer_id']
        self.file_peers[file_name].add(peer_id)
        magnet_link = generate_magnet_link(file_meta, HOST_IP, PORT)

        if not os.path.exists('uploaded_files'):
            os.makedirs('uploaded_files')

        if not os.path.exists(f'uploaded_files/{file_name}.torrent'):
            with open(f'uploaded_files/{file_name}.torrent', 'wb') as torrent_file:
                pickle.dump(file_meta, torrent_file)

        self.send_response(client_socket, UPLOAD_FILE_COMPLETE, magnet_link)

    def handle_file_request(self, client_socket, file_name):
        peer_list = self.file_peers.get(file_name, [])
        if not peer_list:
            self.send_response(client_socket, REQUEST_FILE, "No peers found for the file")
            return

        file_metadata = self.load_torrent_file(file_name)
        peers = [self.get_peer_info(peer_id) for peer_id in peer_list]
        self.send_response(client_socket, SHOW_PEER_HOLD_FILE, {'file_metadata': file_metadata, 'peers': peers})

    def send_file_list(self, client_socket):
        self.send_response(client_socket,SHOW_PEER_HOLD_FILE , list(self.tracked_files))

    def logout_peer(self, client_socket, message):
        peer_id = message['peer_id']
        self.update_client_status(peer_id, 0)
        self.send_response(client_socket, LOGOUT_SUCCESSFUL, "Logged out successfully")

    def send_response(self, client_socket, message_type, message_data):
        response = {'type': message_type, 'data': message_data}
        send_message(client_socket, response)

    def get_client(self, username):
        self.cursor.execute("SELECT * FROM clients WHERE username = ?", (username,))
        return self.cursor.fetchone()

    def get_client_id(self, username):
        self.cursor.execute("SELECT id FROM clients WHERE username = ?", (username,))
        return self.cursor.fetchone()[0]

    def add_new_client(self, username, password, ip, port):
        with self.lock:
            self.cursor.execute("INSERT INTO clients (username, password, ip, port, status) VALUES (?, ?, ?, ?, 0)",
                                (username, password, ip, port))
            self.conn.commit()

    def update_client_status(self, username, ip, port):
        with self.lock:
            self.cursor.execute("UPDATE clients SET ip = ?, port = ?, status = 1 WHERE username = ?", (ip, port, username))
            self.conn.commit()

    def get_peer_info(self, peer_id):
        self.cursor.execute("SELECT ip, port FROM clients WHERE id = ? AND status = 1", (peer_id,))
        return self.cursor.fetchone()

    def load_torrent_file(self, file_name):
        with open(f'uploaded_files/{file_name}.torrent', 'rb') as f:
            return pickle.load(f)

    def run(self):
        print(f"Tracker server listening on {HOST_IP}:{PORT}")
        while True:
            try:
                client_socket, addr = self.server_socket.accept()
                print(f"New connection from {addr}")
                client_thread = threading.Thread(target=self.handle_peer_connection, args=(client_socket, addr))
                client_thread.start()
            except Exception as e:
                print(f"Error accepting connection: {e}")
                traceback.print_exc()
            except KeyboardInterrupt:
                print("Server interrupted")
                break


if __name__ == '__main__':
    tracker = TorrentTracker()
    tracker.run()

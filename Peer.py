import socket
import threading
import sqlite3
import time
import json
import os
import hashlib
import pickle
import struct
import getpass

from Peer_to_peer_communication import *
from Support import *
from Metadata_torent import *

SERVER_NAME = socket.gethostname()
SERVER_IP = socket.gethostbyname(SERVER_NAME)
PORT = 1607

class Peer:
    def __init__(self, ip, port):
        self.ip = ip
        self.port = port
        self.peer_tracker_socket = None
        self.peer_peers_socket = None
        self.user_name = None
        self.peer_id = None
        self.files = {}  # key: file name, value: metain4File
        self.pieces = {}  # key: file name, value: dict of piece index and piece data
        self.magnet_links = {}  # key: file name, value: magnet link

    def tracker_connection(self):
        attempts = 3
        for attempt in range(attempts):
            try:
                self.peer_tracker_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.peer_tracker_socket.connect((SERVER_IP, PORT))
                print(f"The peer has been connected to tracker server at {SERVER_IP}:{PORT}")
                return
            except Exception as e:
                print(f"Attempt {attempt + 1}/{attempts} failed: {e}")
                if attempt < attempts - 1:
                    print("Retrying in 5 seconds...")
                    time.sleep(5)
                else:
                    print("Error connection to tracker after multiple tries.")
                    raise

    def enter_password(self):
        return getpass.getpass("Enter your password: ")

    def signup(self):
        user_name = input("\nEnter your name: ")
        password = self.enter_password()
        msg = {'type': REGISTER, 'user_name': user_name, 'password': password, 'ip': self.ip, 'port': self.port}
        try:
            print("Sign up process is loading...")
            msg = pickle.dumps({'type': REGISTER, 'user_name': user_name, 'password': password, 'ip': self.ip, 'port': self.port})
            self.peer_tracker_socket.sendall(struct.pack('>I', len(msg)) + msg)
            print("Loading....")

            rev_msg = self.receive_message(self.peer_tracker_socket)
            if rev_msg is None:
                raise ConnectionError("Connection close: data received")
            print(f"Received {len(rev_msg)} bytes of data")
            result = pickle.loads(rev_msg)

            if result['type'] == REGISTER_SUCCESSFUL:
                print(f"User: {user_name}\n")
                peer_id = result['peer_id']
                print("Signup successfully!")
                if not os.path.exists(f"repository_{user_name}"):
                    os.makedirs(f"repository_{user_name}")
                    print("We have created your repository")
                else:
                    print("The system already created")
                self.user_name = user_name
                return peer_id
            else:
                print(f"User: {user_name} cant register")
                print(result['message'])
                return None
        except ConnectionResetError:
            print("Connection was reset and closed unexpectedly")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None

    def login(self):
        user_name = input("\nEnter your name: ")
        password = self.enter_password()
        self.user_name = user_name
        msg = {'type': LOGIN, 'user_name': user_name, 'password': password, 'ip': self.ip, 'port': self.port}
        try:
            print("Log in process is loading...")
            msg = pickle.dumps({'type': LOGIN, 'user_name': user_name, 'password': password, 'ip': self.ip, 'port': self.port})
            self.peer_tracker_socket.sendall(struct.pack('>I', len(msg)) + msg)
            print("Loading....")

            rev_msg = self.receive_message(self.peer_tracker_socket)
            if rev_msg is None:
                raise ConnectionError("Connection close: data received")

            print(f"Received {len(rev_msg)} bytes of data")
            result = pickle.loads(rev_msg)
            print(result['type'])
            if result['type'] == LOGIN_SUCCESSFUL:
                print(f"User: {user_name}\n")
                self.peer_id = result['peer_id']
                print("Login successfully!")
                return self.peer_id
            else:
                print(f"User cant login {user_name}")
                print(result['message'])
                if result['type'] == LOGIN_WRONG_PASSWORD:
                    print("The password is incorrect")
                    print("Please try again.")
                    return self.login()
                elif result['type'] == LOGIN_ACC_NOT_EXIST:
                    print("User does not exist. Moving to the signup...")
                    return self.signup()
                else:
                    print("Internal server error")
                    return None
        except Exception as e:
            print(f"Issue occurred during login process: {e}")
        pass
    import os

    def create_torrent(self, file_path: str):
        print("Creating torrent...")
        if not os.path.exists(file_path):
            print(f"File {file_path} does not exist.")
            return

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        info_hash = hashlib.sha1(file_name.encode()).hexdigest()
        pieces = split_file_into_pieces(file_path, PIECE_SIZE)
        tracker_address = f"http://{SERVER_IP}:{PORT}"
        metainfo = {
            'file_name': file_name,
            'file_size': file_size,
            'piece_length': PIECE_SIZE,
            'pieces_count': len(pieces),
            'announce': tracker_address
        }
        self.files[file_name] = metainfo
        self.pieces[file_name] = {i: piece for i, piece in enumerate(pieces)}
        return metainfo

    def upload_file(self):
        if self.peer_id is None:
            print("The peer has to log in first.")
            return

        file_path = str(input("Type file name you want to upload(including format extension): "))
        file_path = 'repository_' + self.user_name + '/' + file_path
        metainfo = self.create_torrent(file_path)
        try:
            print("An upload file request is sending...")

            msg = pickle.dumps({'type': UPLOAD_FILE, 'metainfo': metainfo, 'peer_id': self.peer_id})
            self.peer_tracker_socket.sendall(struct.pack('>I', len(msg)) + msg)

            print("Request has been sent. Awaiting a response from the tracker...")
            rev_msg = self.receive_message(self.peer_tracker_socket)
            if rev_msg is None:
                raise ConnectionError("Close the connection while data is being received")
            print(f"Received {len(rev_msg)} bytes of data")
            result = pickle.loads(rev_msg)
            if result['type'] == UPLOAD_FILE_COMPLETE:
                print(f"File {file_path} uploaded completely")
                magnet_link = result['magnet_link']
                print(f"Magnet link: {magnet_link}")
                with open(os.path.join(f"repository_{self.user_name}", f"{metainfo['file_name']}_magnet"), 'wb') as f:
                    f.write(magnet_link.encode())
            else:
                print(f"File {file_path} cannot upload")
                print(result['message'])
        except Exception as e:
            print(f"An issue occurred during upload file: {e}")

    def receive_message(self, sock):
        try:
            msg_len = struct.unpack('>I', sock.recv(4))[0]
            if msg_len > 0:
                return sock.recv(msg_len)
            else:
                return None
        except Exception as e:
            print(f"An error occurred while receiving the message: {e}")
            return None

    def logout(self):
        if not self.peer_id:
            print("The peer has to log in first.")
            return
        msg = pickle.dumps({'type': LOGOUT, 'peer_id': self.peer_id})
        self.peer_tracker_socket.sendall(struct.pack('>I', len(msg)) + msg)
        print("A logout request has been sent. Awaiting a response from the tracker...")
        rev_msg = self.receive_message(self.peer_tracker_socket)
        if rev_msg is None:
            raise ConnectionError("Close the connection while data is being received")
        result = pickle.loads(rev_msg)
        if result['type'] == LOGOUT_SUCCESSFUL:
            print("Logout completely")
        else:
            print("Cannot log out")
            print(result['message'])

    def tracker_socket(self):
        try:
            self.peer_peers_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.peer_peers_socket.bind((self.ip, self.port))
            self.peer_peers_socket.listen(5)
            print(f"Listening for incoming connections on {self.ip}:{self.port}")
        except Exception as e:
            print(f"There is an error in initializing tracker socket: {e}")

    def clean_up(self):
        try:
            if self.peer_peers_socket:
                self.peer_peers_socket.close()
            if self.peer_tracker_socket:
                self.peer_tracker_socket.close()
        except Exception as e:
            print(f"Error cleaning up: {e}")

    def peer_control(self):
        try:
            self.tracker_socket()
            self.listen_to_peers()
        except Exception as e:
            print(f"Error in peer control: {e}")

    def listen_to_peers(self):
        print("Peer is waiting to connect with peers...")

if __name__ == '__main__':
    peer = Peer(socket.gethostbyname(socket.gethostname()), 1606)
    peer.tracker_connection()
    print("Please choose 1 for Sign Up or 2 for Log In:")
    while True:
        choice = input("Choose 1 or 2: ")
        if choice == '1':
            peer_id = peer.signup()
            if peer_id:
                print(f"Peer ID: {peer_id}")
        elif choice == '2':
            peer_id = peer.login()
            if peer_id:
                print(f"Peer ID: {peer_id}")
                break
        else:
            print("Invalid input. Please try again.")
    peer.peer_control()
   
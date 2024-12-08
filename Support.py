import struct
import pickle
import hashlib
import json  # Thay thế bencodepy để mã hóa/giải mã
import getpass  # Thay thế maskpass để nhập mật khẩu ẩn

def receive_message(socket):
    try:
        data = b""
        while True:
            packet = socket.recv(4096)  # Nhận tối đa 4KB mỗi lần
            if not packet:
                break
            data += packet
            if len(data) >= 4:  # Kiểm tra kích thước dữ liệu, có thể thay đổi theo nhu cầu
                break
        return data
    except Exception as e:
        print(f"An error occurred while receiving the message: {e}")
        return None


def receive_all(sock, n):
    """
    Nhận chính xác n byte từ socket hoặc trả về None nếu không còn dữ liệu.
    """
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data

def enter_password():
    """
    Yêu cầu người dùng nhập mật khẩu và xác nhận mật khẩu, sau đó trả về mật khẩu đã xác nhận.
    """
    while True:
        pwd = getpass.getpass(prompt="Enter your password: ")
        verify = getpass.getpass(prompt="Verify the password: ")

        if pwd == verify:
            print("Password accepted.")
            return pwd
        else:
            print("Passwords do not match. Please try again.")

def send_message(socket, message):
    try:
        # Đóng gói message thành bytes
        data = pickle.dumps(message)
        socket.sendall(data)
    except Exception as e:
        print(f"An error occurred while sending the message: {e}")


def generate_magnet_link(metadata, host, port):
    """
    Tạo một magnet link từ thông tin metadata.
    """
    info_hash = hashlib.sha1(json.dumps(metadata).encode('utf-8')).hexdigest()
    file_name = metadata['file_name']
    file_size = metadata['file_size']

    magnet_link = f"magnet:?xt=urn:btih:{info_hash}&dn={file_name}&xl={file_size}"
    # Thêm tracker URL vào magnet link
    tracker_url = f"http://{host}:{port}/announce"
    magnet_link += f"&tr={tracker_url}"

    return magnet_link

def sha1_hash(data):
    """
    Tính toán hash SHA-1 cho một dữ liệu đầu vào.
    """
    sha1 = hashlib.sha1()
    sha1.update(data)
    return sha1.hexdigest()

def split_file_into_pieces(path, piece_size):
    """
    Chia tệp thành các phần nhỏ và trả về danh sách hash SHA-1 của các phần.
    """
    pieces = []
    with open(path, 'rb') as f:
        while True:
            piece = f.read(piece_size)
            if not piece:
                break
            pieces.append(sha1_hash(piece))
    return pieces

def send_pieces(path, piece_size, indexes):
    """
    Gửi các phần tệp dựa trên danh sách chỉ mục.
    """
    pieces = []
    with open(path, 'rb') as f:
        idx = 0
        while True:
            piece = f.read(piece_size)
            if not piece:
                break
            temp = {'piece': piece, 'id': idx}
            pieces.append(temp)
            idx += 1
    # Lọc chỉ các phần theo chỉ mục yêu cầu
    return [piece for piece in pieces if piece['id'] in indexes]

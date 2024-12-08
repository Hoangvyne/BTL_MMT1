from typing import Dict, Set, List, Tuple
import json  # Sử dụng JSON để encode và decode
import struct  # Đóng gói và giải nén binary
import pickle  # Dùng để serialize dữ liệu phức tạp

HEADER = 10
QUEUE_SIZE = 5
PIECE_SIZE = 512 * 1024  # Kích thước của mỗi phần dữ liệu (mỗi "piece" trong torrent)
FORMAT = 'utf-8'

DISCONNECT_MSG = '!DISCONNECT'

# REGISTER
REGISTER = 'register'
REGISTER_FAILED = 'register_error'
REGISTER_SUCCESSFUL = 'register_completed'
REQUEST = 'request_file'

# LOGIN
LOGIN = 'login'
LOGIN_SUCCESSFUL = 'login_completed'
LOGIN_FAILED = 'login_error'
LOGIN_WRONG_PASSWORD = 'invalid_password'
LOGIN_ACC_NOT_EXIST = 'account_not_found'

# LOGOUT
LOGOUT = 'logout'
LOGOUT_SUCCESSFUL = 'logout_complete'

# UPLOAD FILE
UPLOAD_FILE = 'upload_file'
UPLOAD_FILE_COMPLETE = 'upload_file_complete'
UPLOAD_FILE_ERROR = 'upload_file_error'

# CONTROL
GET_LIST_FILES_TO_DOWNLOAD = 'get_list_files_for_download'  # Lấy danh sách các tệp để tải xuống
DOWNLOAD_FILE = 'download_file'  # Tải xuống tệp
REQUEST_FILE = 'request_file'  # Yêu cầu tệp từ peer
SHOW_PEER_HOLD_FILE = 'show_peer_hold_file'  # Hiển thị các peer đang giữ tệp
SHOW_PEER_HOLD_FILE_FAILED = 'show_peer_hold_file_error'  # Lỗi khi hiển thị các peer giữ tệp
REQUEST_PIECE = 'request_piece'  # Yêu cầu phần dữ liệu (piece) từ peer
SEND_PIECE = 'send_piece'  # Gửi phần dữ liệu (piece) cho peer

# VERIFY
VERIFY_MAGNET_LINK = 'confirm_magnet_link'  # Xác nhận link magnet
VERIFY_MAGNET_LINK_SUCCESSFUL = 'confirm_magnet_link_complete'  # Xác nhận link magnet thành công
VERIFY_MAGNET_LINK_FAILED = 'confirm_magnet_link_complete'  # Xác nhận link magnet thất bại


# Encode data using JSON
def encode_data(data: Dict) -> bytes:
    try:
        json_data = json.dumps(data)  # Convert dictionary to JSON string
        return json_data.encode(FORMAT)  # Encode to bytes
    except Exception as e:
        print(f"Encoding error: {e}")
        return b''

# Decode data using JSON
def decode_data(data: bytes) -> Dict:
    try:
        json_data = data.decode(FORMAT)  # Decode bytes to string
        return json.loads(json_data)  # Convert JSON string to dictionary
    except Exception as e:
        print(f"Decoding error: {e}")
        return {}

# Pack binary data
def pack_data(data: bytes) -> bytes:
    try:
        return struct.pack(f'{len(data)}s', data)  # Pack data with length
    except Exception as e:
        print(f"Packing error: {e}")
        return b''

# Unpack binary data
def unpack_data(data: bytes) -> bytes:
    try:
        return struct.unpack(f'{len(data)}s', data)[0]  # Unpack and return the data
    except Exception as e:
        print(f"Unpacking error: {e}")
        return b''

# Serialize data using pickle
def serialize_data(data) -> bytes:
    try:
        return pickle.dumps(data)  # Serialize data to bytes
    except Exception as e:
        print(f"Serialization error: {e}")
        return b''

# Deserialize data using pickle
def deserialize_data(data: bytes):
    try:
        return pickle.loads(data)  # Deserialize bytes to original object
    except Exception as e:
        print(f"Deserialization error: {e}")
        return None

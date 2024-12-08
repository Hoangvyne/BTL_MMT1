import hashlib  
from dataclasses import dataclass  
from typing import List, Dict
import json  
from Peer_to_peer_communication import *  

@dataclass
class File:
    name: str
    size: int

@dataclass
class Piece:
    index: int
    hash: str

class MetaInfoFile:
    """
    Lớp hỗ trợ xử lý metadata của tệp, bao gồm thông tin hash, danh sách các phần (piece),
    thông tin tệp, và địa chỉ IP của tracker.
    """
    def __init__(self, info_hash: str, pieces: List[Piece], file: File, tracker_ip: str):
        self.info_hash = info_hash
        self.pieces = pieces
        self.file = file
        self.tracker_ip = tracker_ip

    def encode(self) -> bytes:
        """
        Mã hóa thông tin metadata thành chuỗi JSON dạng bytes.
        """
        info = {
            'file_name': self.file.name,
            'file_size': self.file.size,
            'piece_length': PIECE_SIZE,
            'pieces': [piece.hash for piece in self.pieces]
        }
        meta_info = {
            'info': info,
            'tracker_ip': self.tracker_ip
        }
        return json.dumps(meta_info).encode('utf-8')

    @classmethod
    def decode(cls, metainfo: bytes) -> 'MetaInfoFile':
        """
        Giải mã metadata từ chuỗi JSON dạng bytes và tạo ra đối tượng MetaInfoFile.
        """
        decoded = json.loads(metainfo.decode('utf-8'))
        info_hash = hashlib.sha1(json.dumps(decoded['info']).encode('utf-8')).hexdigest()
        pieces = [
            Piece(index=i, hash=piece_hash) 
            for i, piece_hash in enumerate(decoded['info']['pieces'])
        ]
        file = File(name=decoded['info']['file_name'], size=decoded['info']['file_size'])
        return cls(info_hash=info_hash, pieces=pieces, file=file, tracker_ip=decoded['tracker_ip'])

class MagnetLink:
    """
    Lớp xử lý các liên kết magnet (magnet link).
    """
    def __init__(self, info_hash: str, tracker_ip: str):
        self.info_hash = info_hash
        self.tracker_ip = tracker_ip

    def to_string(self) -> str:
        """
        Tạo một chuỗi magnet link từ thông tin hash và IP tracker.
        """
        return f"magnet:?xt=urn:btih:{self.info_hash}&tr={self.tracker_ip}"

    @classmethod
    def decode(cls, magnet_string: str) -> 'MagnetLink':
        """
        Phân tích một magnet link để lấy thông tin hash và IP tracker.
        """
        params = magnet_string.split('&')
        info_hash = params[0].split(':')[-1]
        tracker_ip = params[1].split('=')[-1]
        return cls(info_hash, tracker_ip)

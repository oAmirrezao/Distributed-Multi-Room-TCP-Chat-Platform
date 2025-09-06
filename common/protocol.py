import json
import struct
from enum import Enum
from datetime import datetime

class MessageType(Enum):
    # Authentication
    AUTH_REQUEST = "auth_request"
    AUTH_RESPONSE = "auth_response"
    REGISTER_REQUEST = "register_request"
    REGISTER_RESPONSE = "register_response"
    
    # Room Management
    CREATE_ROOM = "create_room"
    JOIN_ROOM = "join_room"
    LEAVE_ROOM = "leave_room"
    LIST_ROOMS = "list_rooms"
    ROOM_INFO = "room_info"
    
    # Messaging
    TEXT_MESSAGE = "text_message"
    FILE_TRANSFER = "file_transfer"
    FILE_CHUNK = "file_chunk"
    
    # System
    USER_LIST = "user_list"
    SERVER_INFO = "server_info"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    SUCCESS = "success"

class Priority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

class Message:
    def __init__(self, msg_type, data=None, priority=Priority.NORMAL, room_id=None):
        self.id = datetime.now().timestamp()
        self.type = msg_type
        self.data = data or {}
        self.priority = priority
        self.room_id = room_id
        self.timestamp = datetime.now().isoformat()
    
    def to_bytes(self):
        json_data = json.dumps({
            'id': self.id,
            'type': self.type.value,
            'data': self.data,
            'priority': self.priority.value,
            'room_id': self.room_id,
            'timestamp': self.timestamp
        })
        
        json_bytes = json_data.encode('utf-8')
        length = len(json_bytes)
        
        # Protocol: [4 bytes length][json data]
        return struct.pack('!I', length) + json_bytes
    
    @staticmethod
    def from_bytes(data):
        json_data = json.loads(data.decode('utf-8'))
        msg = Message(
            MessageType(json_data['type']),
            json_data['data'],
            Priority(json_data['priority']),
            json_data.get('room_id')
        )
        msg.id = json_data['id']
        msg.timestamp = json_data['timestamp']
        return msg

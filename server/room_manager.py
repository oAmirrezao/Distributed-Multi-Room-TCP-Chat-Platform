import uuid
from datetime import datetime
from collections import defaultdict
import threading

class RoomManager:
    def __init__(self):
        self.rooms = {}  # {room_id: {'name': str, 'users': set, 'created': datetime}}
        self.lock = threading.RLock()
    
    def create_room(self, name):
        with self.lock:
            room_id = str(uuid.uuid4())
            self.rooms[room_id] = {
                'name': name,
                'users': set(),
                'created': datetime.now(),
                'message_count': 0
            }
            return room_id
    
    def join_room(self, room_id, username):
        with self.lock:
            if room_id in self.rooms:
                self.rooms[room_id]['users'].add(username)
                return True
            return False
    
    def leave_room(self, room_id, username):
        with self.lock:
            if room_id in self.rooms:
                self.rooms[room_id]['users'].discard(username)
                
                # Remove empty rooms
                if not self.rooms[room_id]['users']:
                    del self.rooms[room_id]
                return True
            return False
    
    def get_room_users(self, room_id):
        with self.lock:
            if room_id in self.rooms:
                return list(self.rooms[room_id]['users'])
            return []
    
    def list_rooms(self):
        with self.lock:
            return [
                {
                    'id': room_id,
                    'name': info['name'],
                    'user_count': len(info['users']),
                    'created': info['created'].isoformat()
                }
                for room_id, info in self.rooms.items()
            ]
    
    def room_exists(self, room_id):
        with self.lock:
            return room_id in self.rooms

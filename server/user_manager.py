import json
import uuid
from pathlib import Path
import threading
from common.security import SecurityManager
from datetime import datetime

class UserManager:
    def __init__(self, db_file='users.json'):
        self.db_file = Path(db_file)
        self.users = self._load_users()
        self.active_sessions = {}  # {username: session_id}
        self.lock = threading.RLock()
    
    def _load_users(self):
        if self.db_file.exists():
            with open(self.db_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_users(self):
        with open(self.db_file, 'w') as f:
            json.dump(self.users, f)
    
    def register(self, username, password):
        with self.lock:
            if username in self.users:
                return False, None
            
            user_id = str(uuid.uuid4())
            hashed_password = SecurityManager.hash_password(password)
            
            user_data = {
                'id': user_id,
                'username': username,
                'password': hashed_password.decode('utf-8'),
                'created': str(datetime.now())
            }
            
            self.users[username] = user_data
            self._save_users()
            
            return True, user_data
    
    def authenticate(self, username, password):
        with self.lock:
            if username not in self.users:
                return False, None
            
            user_data = self.users[username]
            hashed_password = user_data['password'].encode('utf-8')
            
            if SecurityManager.verify_password(password, hashed_password):
                # Check if already logged in
                if username in self.active_sessions:
                    return False, None  # Prevent multiple sessions
                
                session_id = str(uuid.uuid4())
                self.active_sessions[username] = session_id
                
                return True, user_data
            
            return False, None
    
    def logout(self, username):
        with self.lock:
            if username in self.active_sessions:
                del self.active_sessions[username]

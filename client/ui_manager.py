from datetime import datetime
from colorama import Fore, Back, Style

class UIManager:
    def __init__(self):
        self.show_timestamps = True
    
    def print_message(self, username, text, timestamp=None):
        if not timestamp:
            timestamp = datetime.now().isoformat()
        
        time_str = datetime.fromisoformat(timestamp).strftime('%H:%M:%S')
        print(f"{Fore.CYAN}[{time_str}]{Style.RESET_ALL} {Fore.YELLOW}{username}:{Style.RESET_ALL} {text}")
    
    def print_system(self, text):
        print(f"{Fore.BLUE}[SYSTEM]{Style.RESET_ALL} {text}")
    
    def print_error(self, text):
        print(f"{Fore.RED}[ERROR]{Style.RESET_ALL} {text}")
    
    def print_success(self, text):
        print(f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL} {text}")
    
    def print_room_list(self, rooms):
        if not rooms:
            print("No rooms available")
            return
        
        print(f"\n{Fore.GREEN}Available Rooms:{Style.RESET_ALL}")
        print("-" * 50)
        for room in rooms:
            print(f"ID: {room['id'][:8]}... | Name: {room['name']} | Users: {room['user_count']}")
        print("-" * 50)
    
    def print_user_list(self, users):
        if not users:
            print("No users in room")
            return
        
        print(f"\n{Fore.GREEN}Users in room:{Style.RESET_ALL}")
        for user in users:
            print(f"  - {user}")

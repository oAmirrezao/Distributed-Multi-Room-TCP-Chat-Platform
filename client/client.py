import asyncio
import ssl
import sys
import json
from pathlib import Path
from datetime import datetime
import threading
from colorama import init, Fore, Style

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from common.protocol import Message, MessageType, Priority

# Import from current directory
from ui_manager import UIManager
from file_manager import FileManager

init(autoreset=True)  # Initialize colorama

class ChatClient:
    def __init__(self, host='localhost', port=8888):
        self.host = host
        self.port = port
        self.reader = None
        self.writer = None
        self.ui = UIManager()
        self.file_manager = FileManager()
        self.username = None
        self.current_room = None
        self.running = False
        self.ssl_context = self._create_ssl_context()
    
    def _create_ssl_context(self):
        ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        return ssl_context
    
    async def connect(self):
        try:
            self.reader, self.writer = await asyncio.open_connection(
                self.host, self.port, ssl=self.ssl_context
            )
            self.running = True
            self.ui.print_success("Connected to server")
            
            # Start receiving messages
            asyncio.create_task(self._receive_messages())
            
            # Start heartbeat
            asyncio.create_task(self._send_heartbeat())
            
            return True
        except Exception as e:
            self.ui.print_error(f"Failed to connect: {e}")
            return False
    
    async def _receive_messages(self):
        while self.running:
            try:
                # Read message length
                import struct
                length_data = await self.reader.readexactly(4)
                length = struct.unpack('!I', length_data)[0]
                
                # Read message data
                data = await self.reader.readexactly(length)
                message = Message.from_bytes(data)
                
                await self._handle_message(message)
                
            except asyncio.IncompleteReadError:
                self.ui.print_error("Connection lost")
                break
            except Exception as e:
                self.ui.print_error(f"Error receiving message: {e}")
                break
        
        self.running = False
    
    async def _handle_message(self, message):
        handlers = {
            MessageType.AUTH_RESPONSE: self._handle_auth_response,
            MessageType.REGISTER_RESPONSE: self._handle_register_response,
            MessageType.TEXT_MESSAGE: self._handle_text_message,
            MessageType.USER_LIST: self._handle_user_list,
            MessageType.ROOM_INFO: self._handle_room_info,
            MessageType.SUCCESS: self._handle_success,
            MessageType.ERROR: self._handle_error,
            MessageType.FILE_CHUNK: self._handle_file_chunk,
            MessageType.HEARTBEAT: self._handle_heartbeat,
        }
        
        handler = handlers.get(message.type)
        if handler:
            await handler(message)
    
    async def _send_heartbeat(self):
        while self.running:
            await asyncio.sleep(30)
            await self.send_message(Message(MessageType.HEARTBEAT))
    
    async def send_message(self, message):
        try:
            self.writer.write(message.to_bytes())
            await self.writer.drain()
        except Exception as e:
            self.ui.print_error(f"Failed to send message: {e}")
    
    async def login(self, username, password):
        message = Message(
            MessageType.AUTH_REQUEST,
            {'username': username, 'password': password}
        )
        await self.send_message(message)
    
    async def register(self, username, password):
        message = Message(
            MessageType.REGISTER_REQUEST,
            {'username': username, 'password': password}
        )
        await self.send_message(message)
    
    async def create_room(self, room_name):
        message = Message(
            MessageType.CREATE_ROOM,
            {'name': room_name}
        )
        await self.send_message(message)
    
    async def join_room(self, room_id):
        message = Message(
            MessageType.JOIN_ROOM,
            {'room_id': room_id}
        )
        await self.send_message(message)
    
    async def send_text(self, text):
        if not self.current_room:
            self.ui.print_error("You must join a room first")
            return
        
        message = Message(
            MessageType.TEXT_MESSAGE,
            {'text': text},
            priority=Priority.NORMAL,
            room_id=self.current_room
        )
        await self.send_message(message)
        
        # Display own message
        self.ui.print_message(self.username, text, datetime.now().isoformat())
    
    async def list_rooms(self):
        message = Message(MessageType.LIST_ROOMS)
        await self.send_message(message)
    
    async def list_users(self):
        message = Message(MessageType.USER_LIST)
        await self.send_message(message)
    
    async def send_file(self, file_path):
        if not self.current_room:
            self.ui.print_error("You must join a room first")
            return
        
        chunks = self.file_manager.prepare_file(file_path)
        if not chunks:
            return
        
        for chunk in chunks:
            message = Message(
                MessageType.FILE_TRANSFER,
                chunk,
                priority=Priority.LOW,
                room_id=self.current_room
            )
            await self.send_message(message)
            await asyncio.sleep(0.1)  # Rate limiting
        
        self.ui.print_success(f"File sent: {Path(file_path).name}")
    
    # Message handlers
    async def _handle_auth_response(self, message):
        if message.data['success']:
            self.ui.print_success("Login successful!")
            self.username = message.data.get('username')
        else:
            self.ui.print_error(f"Login failed: {message.data.get('error')}")
    
    async def _handle_register_response(self, message):
        if message.data['success']:
            self.ui.print_success("Registration successful! Please login.")
        else:
            self.ui.print_error(f"Registration failed: {message.data.get('error')}")
    
    async def _handle_text_message(self, message):
        self.ui.print_message(
            message.data['username'],
            message.data['text'],
            message.data['timestamp']
        )
    
    async def _handle_user_list(self, message):
        if 'action' in message.data:
            if message.data['action'] == 'join':
                self.ui.print_system(f"{message.data['username']} joined the room")
            elif message.data['action'] == 'leave':
                self.ui.print_system(f"{message.data['username']} left the room")
        else:
            users = message.data.get('users', [])
            self.ui.print_user_list(users)
    
    async def _handle_room_info(self, message):
        rooms = message.data.get('rooms', [])
        self.ui.print_room_list(rooms)
    
    async def _handle_success(self, message):
        if 'room_id' in message.data:
            self.current_room = message.data['room_id']
            self.ui.print_success(f"Successfully joined room: {message.data.get('name', self.current_room)}")
    
    async def _handle_error(self, message):
        self.ui.print_error(message.data.get('error', 'Unknown error'))
    
    async def _handle_file_chunk(self, message):
        if self.file_manager.receive_chunk(message.data):
            self.ui.print_success(f"File received: {message.data['filename']}")
    
    async def _handle_heartbeat(self, message):
        # Heartbeat response received
        pass
    
    async def disconnect(self):
        self.running = False
        if self.writer:
            self.writer.close()
            await self.writer.wait_closed()
    
    async def run_interactive(self):
        if not await self.connect():
            return
        
        # Show help on start
        await self._show_help()
        
        while self.running:
            try:
                command = await asyncio.get_event_loop().run_in_executor(
                    None, input, f"{Fore.GREEN}> {Style.RESET_ALL}"
                )
                
                if command.strip():
                    if command.startswith('/'):
                        await self._process_command(command)
                    else:
                        await self.send_text(command)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                self.ui.print_error(f"Error: {e}")
        
        await self.disconnect()
    
    async def _process_command(self, command):
        parts = command.split()
        cmd = parts[0].lower()
        
        commands = {
            '/help': self._show_help,
            '/login': lambda: self.login(parts[1], parts[2]) if len(parts) >= 3 else self.ui.print_error("Usage: /login <username> <password>"),
            '/register': lambda: self.register(parts[1], parts[2]) if len(parts) >= 3 else self.ui.print_error("Usage: /register <username> <password>"),
            '/create': lambda: self.create_room(parts[1]) if len(parts) >= 2 else self.ui.print_error("Usage: /create <room_name>"),
            '/join': lambda: self.join_room(parts[1]) if len(parts) >= 2 else self.ui.print_error("Usage: /join <room_id>"),
            '/rooms': self.list_rooms,
            '/users': self.list_users,
            '/file': lambda: self.send_file(parts[1]) if len(parts) >= 2 else self.ui.print_error("Usage: /file <path>"),
            '/quit': self._quit
        }
        
        if cmd in commands:
            result = commands[cmd]()
            if asyncio.iscoroutine(result):
                await result
        else:
            self.ui.print_error(f"Unknown command: {cmd}")
    
    async def _show_help(self):
        help_text = """
Available commands:
  /help                     - Show this help message
  /login <user> <pass>      - Login with username and password
  /register <user> <pass>   - Register new account
  /create <name>            - Create a new room
  /join <room_id>          - Join a room
  /rooms                   - List all rooms
  /users                   - List users in current room
  /file <path>             - Send a file
  /quit                    - Quit the application
        """
        self.ui.print_system(help_text)
    
    async def _quit(self):
        self.running = False

if __name__ == "__main__":
    client = ChatClient()
    try:
        asyncio.run(client.run_interactive())
    except KeyboardInterrupt:
        print("\nGoodbye!")

import asyncio
import ssl
import json
import logging
import time
from datetime import datetime
from collections import defaultdict
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from common.protocol import Message, MessageType, Priority
from common.security import SecurityManager

# Import from current directory
from room_manager import RoomManager
from user_manager import UserManager
from qos_manager import QoSManager
from performance_monitor import PerformanceMonitor

class ChatServer:
    def __init__(self, host='0.0.0.0', port=8888):
        self.host = host
        self.port = port
        self.clients = {}  # {client_id: {'writer': writer, 'user': user_info, 'room_id': room_id}}
        self.room_manager = RoomManager()
        self.user_manager = UserManager()
        self.qos_manager = QoSManager()
        self.performance_monitor = PerformanceMonitor()
        
        # Create logs directory if it doesn't exist
        Path('logs').mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('logs/server.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # SSL context
        self.ssl_context = self._create_ssl_context()
    
    def _create_ssl_context(self):
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.load_cert_chain(
            'certificates/server-cert.pem',
            'certificates/server-key.pem'
        )
        return ssl_context
    
    async def handle_client(self, reader, writer):
        client_addr = writer.get_extra_info('peername')
        client_id = f"{client_addr[0]}:{client_addr[1]}_{time.time()}"
        
        self.logger.info(f"New connection from {client_addr}")
        self.performance_monitor.record_connection()
        
        try:
            await self._client_loop(client_id, reader, writer)
        except asyncio.CancelledError:
            pass
        except Exception as e:
            self.logger.error(f"Error handling client {client_id}: {e}")
        finally:
            await self._disconnect_client(client_id)
    
    async def _client_loop(self, client_id, reader, writer):
        while True:
            try:
                # Read message length
                length_data = await reader.readexactly(4)
                if not length_data:
                    break
                
                import struct
                length = struct.unpack('!I', length_data)[0]
                
                # Read message data
                data = await reader.readexactly(length)
                message = Message.from_bytes(data)
                
                # Record metrics
                self.performance_monitor.record_message(len(data))
                
                # Process message with QoS
                await self.qos_manager.enqueue(
                    self._process_message,
                    client_id,
                    message,
                    writer,
                    priority=message.priority
                )
                
            except asyncio.IncompleteReadError:
                break
            except Exception as e:
                self.logger.error(f"Error reading from client {client_id}: {e}")
                break
    
    async def _process_message(self, client_id, message, writer):
        start_time = time.time()
        
        handlers = {
            MessageType.AUTH_REQUEST: self._handle_auth,
            MessageType.REGISTER_REQUEST: self._handle_register,
            MessageType.CREATE_ROOM: self._handle_create_room,
            MessageType.JOIN_ROOM: self._handle_join_room,
            MessageType.LEAVE_ROOM: self._handle_leave_room,
            MessageType.LIST_ROOMS: self._handle_list_rooms,
            MessageType.TEXT_MESSAGE: self._handle_text_message,
            MessageType.FILE_TRANSFER: self._handle_file_transfer,
            MessageType.USER_LIST: self._handle_user_list,
            MessageType.HEARTBEAT: self._handle_heartbeat,
        }
        
        handler = handlers.get(message.type)
        if handler:
            await handler(client_id, message, writer)
        
        # Record processing time
        processing_time = time.time() - start_time
        self.performance_monitor.record_processing_time(processing_time)
    
    async def _handle_auth(self, client_id, message, writer):
        username = message.data.get('username')
        password = message.data.get('password')
        
        success, user_data = self.user_manager.authenticate(username, password)
        
        if success:
            self.clients[client_id] = {
                'writer': writer,
                'user': user_data,
                'room_id': None,
                'last_heartbeat': time.time()
            }
            
            response = Message(
                MessageType.AUTH_RESPONSE,
                {'success': True, 'user_id': user_data['id'], 'username': username}
            )
            self.logger.info(f"User {username} authenticated")
        else:
            response = Message(
                MessageType.AUTH_RESPONSE,
                {'success': False, 'error': 'Invalid credentials'}
            )
        
        await self._send_message(writer, response)
    
    async def _handle_register(self, client_id, message, writer):
        username = message.data.get('username')
        password = message.data.get('password')
        
        success, user_data = self.user_manager.register(username, password)
        
        if success:
            response = Message(
                MessageType.REGISTER_RESPONSE,
                {'success': True, 'user_id': user_data['id']}
            )
            self.logger.info(f"User {username} registered")
        else:
            response = Message(
                MessageType.REGISTER_RESPONSE,
                {'success': False, 'error': 'Username already exists'}
            )
        
        await self._send_message(writer, response)
    
    async def _handle_create_room(self, client_id, message, writer):
        if client_id not in self.clients:
            return
        
        room_name = message.data.get('name')
        room_id = self.room_manager.create_room(room_name)
        
        response = Message(
            MessageType.SUCCESS,
            {'room_id': room_id, 'name': room_name}
        )
        await self._send_message(writer, response)
        
        self.logger.info(f"Room '{room_name}' created with ID: {room_id}")
    
    async def _handle_join_room(self, client_id, message, writer):
        if client_id not in self.clients:
            return
        
        room_id = message.data.get('room_id')
        user_info = self.clients[client_id]['user']
        
        if self.room_manager.join_room(room_id, user_info['username']):
            self.clients[client_id]['room_id'] = room_id
            
            # Notify other users in room
            await self._broadcast_to_room(
                room_id,
                Message(
                    MessageType.USER_LIST,
                    {'action': 'join', 'username': user_info['username']},
                    room_id=room_id
                ),
                exclude_client=client_id
            )
            
            response = Message(
                MessageType.SUCCESS,
                {'room_id': room_id}
            )
        else:
            response = Message(
                MessageType.ERROR,
                {'error': 'Failed to join room'}
            )
        
        await self._send_message(writer, response)
    
    async def _handle_leave_room(self, client_id, message, writer):
        # Implementation for leaving room
        pass
    
    async def _handle_text_message(self, client_id, message, writer):
        if client_id not in self.clients:
            return
        
        client_info = self.clients[client_id]
        room_id = client_info['room_id']
        
        if not room_id:
            error_msg = Message(
                MessageType.ERROR,
                {'error': 'Not in a room'}
            )
            await self._send_message(writer, error_msg)
            return
        
        broadcast_msg = Message(
            MessageType.TEXT_MESSAGE,
            {
                'username': client_info['user']['username'],
                'text': message.data.get('text'),
                'timestamp': datetime.now().isoformat()
            },
            room_id=room_id
        )
        
        await self._broadcast_to_room(room_id, broadcast_msg, exclude_client=client_id)
    
    async def _handle_list_rooms(self, client_id, message, writer):
        rooms = self.room_manager.list_rooms()
        response = Message(
            MessageType.ROOM_INFO,
            {'rooms': rooms}
        )
        await self._send_message(writer, response)
    
    async def _handle_user_list(self, client_id, message, writer):
        if client_id not in self.clients:
            return
        
        room_id = self.clients[client_id]['room_id']
        if room_id:
            users = self.room_manager.get_room_users(room_id)
            response = Message(
                MessageType.USER_LIST,
                {'users': users}
            )
            await self._send_message(writer, response)
    
    async def _handle_file_transfer(self, client_id, message, writer):
        # Implementation for file transfer
        if client_id not in self.clients:
            return
        
        client_info = self.clients[client_id]
        room_id = client_info['room_id']
        
        if not room_id:
            error_msg = Message(
                MessageType.ERROR,
                {'error': 'Not in a room'}
            )
            await self._send_message(writer, error_msg)
            return
        
        # Broadcast file chunk to room
        file_msg = Message(
            MessageType.FILE_CHUNK,
            message.data,
            priority=Priority.LOW,
            room_id=room_id
        )
        
        await self._broadcast_to_room(room_id, file_msg, exclude_client=client_id)
    
    async def _handle_heartbeat(self, client_id, message, writer):
        if client_id in self.clients:
            self.clients[client_id]['last_heartbeat'] = time.time()
        
        response = Message(MessageType.HEARTBEAT)
        await self._send_message(writer, response)
    
    async def _broadcast_to_room(self, room_id, message, exclude_client=None):
        tasks = []
        for client_id, client_info in self.clients.items():
            if client_info['room_id'] == room_id and client_id != exclude_client:
                tasks.append(
                    self._send_message(client_info['writer'], message)
                )
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _send_message(self, writer, message):
        try:
            writer.write(message.to_bytes())
            await writer.drain()
        except Exception as e:
            self.logger.error(f"Error sending message: {e}")
    
    async def _disconnect_client(self, client_id):
        if client_id in self.clients:
            client_info = self.clients[client_id]
            room_id = client_info['room_id']
            username = client_info['user']['username']
            
            # Logout user
            self.user_manager.logout(username)
            
            # Remove from room
            if room_id:
                self.room_manager.leave_room(room_id, username)
                
                # Notify others
                await self._broadcast_to_room(
                    room_id,
                    Message(
                        MessageType.USER_LIST,
                        {'action': 'leave', 'username': username},
                        room_id=room_id
                    )
                )
            
            # Close connection
            try:
                client_info['writer'].close()
                await client_info['writer'].wait_closed()
            except:
                pass
            
            del self.clients[client_id]
            self.performance_monitor.record_disconnection()
            self.logger.info(f"Client {client_id} disconnected")
    
    async def cleanup_inactive_clients(self):
        """Remove inactive clients (no heartbeat for 60 seconds)"""
        while True:
            await asyncio.sleep(30)
            current_time = time.time()
            
            inactive_clients = [
                client_id for client_id, info in self.clients.items()
                if current_time - info.get('last_heartbeat', current_time) > 60
            ]
            
            for client_id in inactive_clients:
                self.logger.info(f"Removing inactive client: {client_id}")
                await self._disconnect_client(client_id)
    
    async def start(self):
        server = await asyncio.start_server(
            self.handle_client,
            self.host,
            self.port,
            ssl=self.ssl_context
        )
        
        self.logger.info(f"Server started on {self.host}:{self.port}")
        
        # Start background tasks
        asyncio.create_task(self.cleanup_inactive_clients())
        asyncio.create_task(self.performance_monitor.report_stats())
        # asyncio.create_task(self.performance_monitor.generate_graphs()) # Removed
        
        async with server:
            await server.serve_forever()

if __name__ == "__main__":
    server = ChatServer()
    try:
        asyncio.run(server.start())
    except KeyboardInterrupt:
        print("\nShutting down server...")

import asyncio
import sys
import time
import random
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from client.client import ChatClient

class LoadTester:
    def __init__(self, num_clients=10, server_host='localhost', server_port=8888):
        self.num_clients = num_clients
        self.server_host = server_host
        self.server_port = server_port
        self.clients = []
        self.stats = {
            'connected': 0,
            'messages_sent': 0,
            'errors': 0,
            'start_time': time.time()
        }
    
    async def create_test_client(self, client_id):
        client = ChatClient(self.server_host, self.server_port)
        
        try:
            # Connect
            if await client.connect():
                self.stats['connected'] += 1
                
                # Register and login
                username = f"testuser_{client_id}"
                password = "testpass123"
                
                await client.register(username, password)
                await asyncio.sleep(0.5)
                await client.login(username, password)
                await asyncio.sleep(0.5)
                
                # Create or join room
                if client_id == 0:
                    await client.create_room("TestRoom")
                    await asyncio.sleep(1)
                
                await client.join_room("test_room_id")  # You'll need to capture this
                
                # Send messages
                for i in range(10):
                    await client.send_text(f"Test message {i} from client {client_id}")
                    self.stats['messages_sent'] += 1
                    await asyncio.sleep(random.uniform(1, 3))
                
                return client
                
        except Exception as e:
            print(f"Error in client {client_id}: {e}")
            self.stats['errors'] += 1
            return None
    
    async def run_test(self):
        print(f"Starting load test with {self.num_clients} clients...")
        
        # Create clients concurrently
        tasks = [self.create_test_client(i) for i in range(self.num_clients)]
        self.clients = await asyncio.gather(*tasks)
        
        # Remove failed clients
        self.clients = [c for c in self.clients if c is not None]
        
        # Keep clients running for a while
        await asyncio.sleep(30)
        
        # Disconnect all clients
        disconnect_tasks = [client.disconnect() for client in self.clients]
        await asyncio.gather(*disconnect_tasks)
        
        # Print statistics
        duration = time.time() - self.stats['start_time']
        print(f"\nLoad Test Results:")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Clients connected: {self.stats['connected']}/{self.num_clients}")
        print(f"Messages sent: {self.stats['messages_sent']}")
        print(f"Errors: {self.stats['errors']}")
        print(f"Messages per second: {self.stats['messages_sent']/duration:.2f}")

if __name__ == "__main__":
    num_clients = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    tester = LoadTester(num_clients=num_clients)
    asyncio.run(tester.run_test())

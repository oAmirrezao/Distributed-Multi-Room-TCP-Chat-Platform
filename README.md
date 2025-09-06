<img width="1198" height="769" alt="Screenshot from 2025-09-06 15-44-47" src="https://github.com/user-attachments/assets/2a1b60b6-8fe5-4b24-abea-e16c5adf7ad4" />
<img width="1210" height="778" alt="Screenshot from 2025-09-06 15-47-34" src="https://github.com/user-attachments/assets/345713cf-92f2-4d79-a6ed-91fc7b7eaa4d" />


# Distributed Multi-Room TCP Chat Platform

A comprehensive, secure, and scalable chat platform implementing advanced networking concepts including multi-room architecture, TLS encryption, Quality of Service (QoS), and performance monitoring.

## Features

### Core Functionality
- **Multi-room chat system** with dynamic room creation and management
- **Secure authentication** using bcrypt password hashing
- **TLS encryption** for all client-server communications
- **File transfer support** with chunking and reassembly
- **Real-time user presence** tracking

### Advanced Features
- **Quality of Service (QoS)** with priority-based message queuing
- **Performance monitoring** with real-time metrics and visualization
- **Load balancing** capabilities for horizontal scaling
- **Comprehensive logging** and analytics
- **Automatic client reconnection** and heartbeat monitoring

## Architecture

### Server Components
- **Main Server**: Handles client connections and message routing
- **Room Manager**: Manages chat rooms and user memberships
- **User Manager**: Handles authentication and user sessions
- **QoS Manager**: Implements priority-based message processing
- **Performance Monitor**: Tracks and reports system metrics

### Client Components
- **Chat Client**: Main client application with async I/O
- **UI Manager**: Handles terminal-based user interface
- **File Manager**: Manages file transfers and storage

## Installation

### Prerequisites
```
# Ubuntu 22.04
sudo apt update
sudo apt install python3-pip python3-dev openssl

# Python packages
pip3 install -r requirements.txt
```

### SSL Certificate Generation
```
cd certificates
openssl req -x509 -newkey rsa:4096 -keyout server-key.pem -out server-cert.pem -days 365 -nodes
```
## Usage

### Starting the Server
```
python3 server/server.py
```

### Running the Client
```
python3 client/client.py
```

### Client Commands
- `/help` - Show available commands
- `/register <username> <password>` - Create new account
- `/login <username> <password>` - Login to existing account
- `/create <room_name>` - Create a new chat room
- `/join <room_id>` - Join an existing room
- `/rooms` - List all available rooms
- `/users` - List users in current room
- `/file <path>` - Send a file to current room
- `/quit` - Exit the application

## Performance Testing

### Load Testing
```
# Run load test with 50 concurrent clients
python3 tests/load_test.py 50
```

### Security Testing
```
# Test SSL encryption and authentication
sudo python3 tests/security_test.py
```

## Monitoring

Performance metrics are automatically collected and saved to:
- `logs/server.log` - Server activity logs
- `logs/performance_stats.json` - Performance metrics
- `monitoring/graphs/` - Performance visualization graphs

## Technical Implementation

### Network Protocol
- Custom application-layer protocol over TCP
- Message format: `[4-byte length][JSON payload]`
- Support for different message types and priorities

### Security Features
- TLS 1.3 encryption for all communications
- Bcrypt password hashing with salt
- Session management to prevent duplicate logins
- Input validation and sanitization

### QoS Implementation
- Four priority levels: Critical, High, Normal, Low
- Priority queue implementation using Python heapq
- Configurable concurrent task limits

### Performance Optimizations
- Asynchronous I/O using Python asyncio
- Connection pooling and reuse
- Efficient binary protocol for file transfers
- Message batching for improved throughput

## Scalability

The platform supports horizontal scaling through:
- Multiple server instances
- Redis-based session sharing (future enhancement)
- Load balancer integration support

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.


## مرحله 9: اجرای پروژه

### 1. اجرای سرور:

```
cd ~/distributed-chat-platform
python3 server/server.py
```
### 2. اجرای کلاینت(در ترمینال جدید):
```
cd ~/distributed-chat-platform
python3 client/client.py
```

### 3. سناریوی تست کامل:
```
import asyncio
import ssl
import sys
import json
from pathlib import Path
from datetime import datetime
import threading
from colorama import init, Fore, Style

sys.path.append(str(Path(__file__).parent.parent))

from common.protocol import Message, MessageType, Priority

# Import from current directory
from ui_manager import UIManager
from file_manager import FileManager
```

### 4. اجرای تست بار:

```
python3 tests/load_test.py 20
```

### 5. مشاهده گراف‌های عملکرد:

```
ls monitoring/graphs/
# مشاهده با image viewer
xdg-open monitoring/graphs/processing_times.png
```



![Uploading Screenshot from 2025-09-06 15-47-34.png…]()

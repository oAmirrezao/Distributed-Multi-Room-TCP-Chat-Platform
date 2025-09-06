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
```bash
# Ubuntu 22.04
sudo apt update
sudo apt install python3-pip python3-dev openssl

# Python packages
pip3 install -r requirements.txt

### SSL Certificate Generation
bash
cd certificates
openssl req -x509 -newkey rsa:4096 -keyout server-key.pem -out server-cert.pem -days 365 -nodes

## Usage

### Starting the Server
bash
python3 server/server.py

### Running the Client
bash
python3 client/client.py

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
bash
# Run load test with 50 concurrent clients
python3 tests/load_test.py 50

### Security Testing
bash
# Test SSL encryption and authentication
sudo python3 tests/security_test.py

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

bash```
cd ~/distributed-chat-platform
python3 server/server.py
```

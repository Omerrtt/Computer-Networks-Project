# Quiz Game - Client-Server Application

This project is a client-server application where multiple clients can connect and play a quiz game together.

## Requirements

- Python 3.6 or higher
- tkinter (usually comes with Python)

## Installation

1. Copy the project files to a directory
2. Make sure Python is installed
3. No additional package installation required (only standard libraries are used)

## Usage

### Starting the Server

1. Run the `server.py` file:
   ```bash
   python server.py
   ```

2. In the Server GUI:
   - Enter the port number (default: 12345)
   - Click the "Start Server" button
   - Enter the number of questions to be asked
   - The "Start Game" button will be enabled when at least 2 clients are connected

### Starting the Client

1. Run the `client.py` file for each client:
   ```bash
   python client.py
   ```

2. In the Client GUI:
   - Enter the Server IP address (if testing on the same computer: 127.0.0.1)
   - Enter the port number (the port the server is listening on)
   - Enter a unique username
   - Click the "Connect" button

### Game Rules

- Select one of the A, B, C options for each question
- Click the "Submit Answer" button to send your answer
- Correct answer: 1 point
- First correct answer: Bonus points (number of players - 1)
- Results are not shown until all players have answered
- The game ends when the designated number of questions is completed or fewer than 2 players remain

## Question Format

Questions are embedded directly in the server code. The server contains 10 pre-loaded questions. The format used is:
- Question text
- A - Choice A
- B - Choice B
- C - Choice C
- Answer: [A/B/C]

## Features

- ✅ TCP socket communication
- ✅ Multiple client support
- ✅ Unique username validation
- ✅ Real-time scoreboard
- ✅ First correct answer bonus points
- ✅ Connection disconnection handling
- ✅ Detailed activity logs
- ✅ Ranking system (ties are supported)

## Notes

- Server and clients can be run on different computers
- New connections are not accepted after the game has started
- If a player disconnects, other players are notified
- The game ends if fewer than 2 players remain during the game

## Connecting from Different Computers

To connect from a different computer:

1. **Find the Server IP Address** (on the server computer):
   - Windows: Open Command Prompt and run `ipconfig`
   - Look for "IPv4 Address" (e.g., 192.168.1.100)

2. **Configure Firewall** (on the server computer):
   - Allow incoming connections on the port (default: 12345)
   - Or temporarily disable firewall for testing

3. **Connect from Client**:
   - Enter the server's IP address in the Client GUI
   - Enter the same port number
   - Enter a unique username
   - Click "Connect"

**Important**: Both computers must be on the same network (same Wi-Fi/router).

## Testing

1. Start the server
2. Start at least 2 clients and connect
3. Click "Start Game" on the server
4. Answer questions and track scores

## Troubleshooting

- **Connection error**: Make sure the server is running and you entered the correct IP/Port
- **Name error**: Use a different username for each client
- **Timeout error**: Check firewall settings or verify the IP address is correct

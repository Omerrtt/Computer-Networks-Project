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
   
   **Windows Firewall Settings:**
   
   **Method 1: Via PowerShell (Recommended)**
   - Open PowerShell as **Administrator**
   - Run the following command:
     ```powershell
     New-NetFirewallRule -DisplayName "Quiz Server - Port 12345" -Direction Inbound -Protocol TCP -LocalPort 12345 -Action Allow -Profile Any
     ```
   - Or run the `firewall_setup.ps1` script in the project folder as administrator
   
   **Method 2: Via Windows Defender Firewall GUI**
   - Press Windows Key + R, type `wf.msc` and press Enter
   - Select "Inbound Rules" from the left side
   - Click "New Rule" from the right side
   - Select "Port", Next
   - Select "TCP", select "Specific local ports"
   - Port number: `12345`, Next
   - Select "Allow the connection", Next
   - Check all profiles (Domain, Private, Public), Next
   - Name: "Quiz Server - Port 12345", Finish
   
   **Note:** If firewall settings are not configured, the client cannot connect!

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

### "Connection timeout" Error (Connecting from Mac to Windows)

This error is usually caused by the following reasons. Check the steps below in order:

#### 1. Windows Firewall Check (On Server Laptop)

**Check if the firewall rule is added:**
```powershell
# Open PowerShell as administrator and run:
.\check_firewall.ps1
```

If the rule does not exist, add it:
```powershell
New-NetFirewallRule -DisplayName "Quiz Server - Port 12345" -Direction Inbound -Protocol TCP -LocalPort 12345 -Action Allow -Profile Any
```

#### 2. Verify Server IP Address (On Windows Laptop)

**While Server is running:**
- Note the IP address shown in the Server GUI
- Or run the following command in Command Prompt:
  ```cmd
  ipconfig
  ```
- Find the "IPv4 Address" value (e.g., 192.168.1.100)
- **Do not use 127.0.0.1 or localhost!** This is only for connecting from the same computer.

#### 3. Test Network Connection

**Ping the Windows laptop from the Mac laptop:**
```bash
# In Mac Terminal:
ping [WINDOWS_IP_ADDRESS]
# Example: ping 192.168.1.100
```

If ping fails:
- Both laptops must be on the same Wi-Fi network
- They cannot connect if on different networks (e.g., one on Wi-Fi, one on ethernet)

#### 4. Test Port Connection

**On Windows laptop (While Server is running):**
```bash
python test_connection.py 127.0.0.1 12345
```

**From Mac laptop:**
```bash
python test_connection.py [WINDOWS_IP_ADDRESS] 12345
# Example: python test_connection.py 192.168.1.100 12345
```

#### 5. Verify Server is Running

- You should see "Server started and listening on port 12345" message in Server GUI
- "Connected Clients" list should be empty (if no one connected yet)
- Server IP address should be shown correctly

#### 6. Mac Client Settings

When running client.py on Mac:
- **Server IP:** Windows laptop's IP address (NOT 127.0.0.1!)
- **Port:** 12345 (or whatever port you set on server)
- **Username:** A unique name

### Other Errors

- **Connection error**: Check if Server is running, IP/Port correct?
- **Name error**: Use a different username for each client
- **Connection refused**: Server not running or wrong port
- **Timeout error**: 
  1. Check firewall settings
  2. Ensure IP address is correct
  3. Verify both laptops are on the same network
  4. Check if Server is running

### Quick Checklist

When connecting from Mac to Windows:

- [ ] server.py is running on Windows laptop
- [ ] Port 12345 is open in Windows Firewall
- [ ] Mac and Windows are on the same Wi-Fi network
- [ ] Ping from Mac to Windows is successful
- [ ] Correct IP address entered in Client (not 127.0.0.1!)
- [ ] Correct port entered in Client (12345)
- [ ] Username is unique

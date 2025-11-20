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
   
   **Windows Firewall Ayarları:**
   
   **Yöntem 1: PowerShell ile (Önerilen)**
   - PowerShell'i **Yönetici olarak** açın
   - Şu komutu çalıştırın:
     ```powershell
     New-NetFirewallRule -DisplayName "Quiz Server - Port 12345" -Direction Inbound -Protocol TCP -LocalPort 12345 -Action Allow -Profile Any
     ```
   - Veya proje klasöründeki `firewall_setup.ps1` script'ini yönetici olarak çalıştırın
   
   **Yöntem 2: Windows Defender Firewall GUI ile**
   - Windows tuşu + R, `wf.msc` yazıp Enter
   - Sol taraftan "Gelen Kurallar" (Inbound Rules) seçin
   - Sağ taraftan "Yeni Kural" (New Rule) tıklayın
   - "Port" seçeneğini seçin, İleri
   - "TCP" seçin, "Belirli yerel bağlantı noktaları" (Specific local ports) seçin
   - Port numarası: `12345`, İleri
   - "Bağlantıya izin ver" (Allow the connection) seçin, İleri
   - Tüm profilleri işaretleyin (Domain, Private, Public), İleri
   - İsim: "Quiz Server - Port 12345", Son
   
   **Not:** Firewall ayarları yapılmazsa client bağlanamaz!

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

### "Connection timeout" Hatası (Mac'ten Windows'a Bağlanırken)

Bu hata genellikle şu nedenlerden kaynaklanır. Aşağıdaki adımları sırayla kontrol edin:

#### 1. Windows Firewall Kontrolü (Server Laptop'ta)

**Firewall kuralının ekli olduğunu kontrol edin:**
```powershell
# PowerShell'i yönetici olarak açın ve çalıştırın:
.\check_firewall.ps1
```

Eğer kural yoksa, ekleyin:
```powershell
New-NetFirewallRule -DisplayName "Quiz Server - Port 12345" -Direction Inbound -Protocol TCP -LocalPort 12345 -Action Allow -Profile Any
```

#### 2. Server'ın IP Adresini Doğrulama (Windows Laptop'ta)

**Server çalışırken:**
- Server GUI'de gösterilen IP adresini not edin
- Veya Command Prompt'ta şu komutu çalıştırın:
  ```cmd
  ipconfig
  ```
- "IPv4 Address" değerini bulun (örn: 192.168.1.100)
- **127.0.0.1 veya localhost kullanmayın!** Bu sadece aynı bilgisayardan bağlanmak için.

#### 3. Ağ Bağlantısını Test Etme

**Mac laptop'tan Windows laptop'a ping atın:**
```bash
# Mac Terminal'de:
ping [WINDOWS_IP_ADDRESS]
# Örnek: ping 192.168.1.100
```

Eğer ping başarısız olursa:
- İki laptop aynı Wi-Fi ağında olmalı
- Farklı ağlardaysa (örn: biri Wi-Fi, diğeri ethernet) bağlanamaz

#### 4. Port Bağlantısını Test Etme

**Windows laptop'ta (Server çalışırken):**
```bash
python test_connection.py 127.0.0.1 12345
```

**Mac laptop'tan:**
```bash
python test_connection.py [WINDOWS_IP_ADDRESS] 12345
# Örnek: python test_connection.py 192.168.1.100 12345
```

#### 5. Server'ın Çalıştığını Doğrulama

- Server GUI'de "Server started and listening on port 12345" mesajını görmelisiniz
- "Connected Clients" listesi boş olmalı (henüz bağlanan yoksa)
- Server'ın IP adresi doğru gösterilmeli

#### 6. Mac Client Ayarları

Mac'te client.py'yi çalıştırırken:
- **Server IP:** Windows laptop'ın IP adresi (127.0.0.1 DEĞİL!)
- **Port:** 12345 (veya server'da ayarladığınız port)
- **Username:** Benzersiz bir isim

### Diğer Hatalar

- **Connection error**: Server çalışıyor mu kontrol edin, IP/Port doğru mu?
- **Name error**: Her client için farklı bir username kullanın
- **Connection refused**: Server çalışmıyor veya yanlış port
- **Timeout error**: 
  1. Firewall ayarlarını kontrol edin
  2. IP adresinin doğru olduğundan emin olun
  3. İki laptop'ın aynı ağda olduğunu doğrulayın
  4. Server'ın çalıştığını kontrol edin

### Hızlı Kontrol Listesi

Mac'ten Windows'a bağlanırken:

- [ ] Windows laptop'ta server.py çalışıyor
- [ ] Windows Firewall'da port 12345 açık
- [ ] Mac ve Windows aynı Wi-Fi ağında
- [ ] Mac'ten Windows'a ping başarılı
- [ ] Client'ta doğru IP adresi girildi (127.0.0.1 değil!)
- [ ] Client'ta doğru port girildi (12345)
- [ ] Username benzersiz

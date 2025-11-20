"""
Bağlantı Test Scripti
Bu script server'ın çalışıp çalışmadığını ve portun açık olup olmadığını test eder.
"""
import socket
import sys

def test_port(host, port, timeout=5):
    """Belirtilen host ve port'a bağlanmayı dener"""
    try:
        print(f"Testing connection to {host}:{port}...")
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        result = sock.connect_ex((host, port))
        sock.close()
        
        if result == 0:
            print(f"✅ SUCCESS: Port {port} is OPEN and reachable!")
            return True
        else:
            print(f"❌ FAILED: Port {port} is CLOSED or unreachable (Error code: {result})")
            return False
    except socket.timeout:
        print(f"❌ TIMEOUT: Connection timed out after {timeout} seconds")
        print("   Possible causes:")
        print("   - Firewall is blocking the connection")
        print("   - Server is not running")
        print("   - Wrong IP address")
        print("   - Different network")
        return False
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return False

def get_local_ip():
    """Yerel IP adresini bulur"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "Unable to determine"

if __name__ == "__main__":
    print("=" * 60)
    print("Quiz Server Connection Test")
    print("=" * 60)
    print()
    
    # Yerel IP'yi göster
    local_ip = get_local_ip()
    print(f"Your local IP address: {local_ip}")
    print()
    
    # Kullanıcıdan bilgi al
    if len(sys.argv) >= 3:
        server_ip = sys.argv[1]
        port = int(sys.argv[2])
    else:
        server_ip = input("Enter server IP address (or press Enter for localhost): ").strip()
        if not server_ip:
            server_ip = "127.0.0.1"
        
        port_str = input("Enter port number (default 12345): ").strip()
        port = int(port_str) if port_str else 12345
    
    print()
    print(f"Testing connection to {server_ip}:{port}")
    print("-" * 60)
    
    success = test_port(server_ip, port)
    
    print("-" * 60)
    if success:
        print("✅ Connection test PASSED!")
        print("   You should be able to connect from the client.")
    else:
        print("❌ Connection test FAILED!")
        print()
        print("Troubleshooting steps:")
        print("1. Make sure server.py is running on the server computer")
        print("2. Check if Windows Firewall is blocking port", port)
        print("3. Verify the IP address is correct")
        print("4. Make sure both computers are on the same network")
        print("5. Try pinging the server: ping", server_ip)
    
    print("=" * 60)


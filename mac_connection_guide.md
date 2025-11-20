# Mac'ten Windows'a Bağlanma Rehberi

## Adım 1: Mac'te Ağ Kontrolü

Mac Terminal'de şu komutları çalıştırın:

### 1. Mac'in IP adresini öğrenin:
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### 2. Windows laptop'a ping atın:
```bash
ping 10.51.113.149
```

**Eğer ping başarısız olursa:**
- İki laptop aynı Wi-Fi ağında değil
- Farklı ağlardaysa bağlanamazsınız

### 3. Port bağlantısını test edin:

Mac Terminal'de (proje klasöründe):
```bash
python test_connection.py 10.51.113.149 12345
```

**Beklenen sonuç:** ✅ SUCCESS

**Eğer ❌ FAILED veya TIMEOUT alırsanız:**
- Windows Firewall sorunu olabilir
- Ağ sorunu olabilir

## Adım 2: Windows Firewall Kontrolü

Windows laptop'ta PowerShell'i **Yönetici olarak** açın ve çalıştırın:

```powershell
# Mevcut kuralı kontrol et
Get-NetFirewallRule -DisplayName "Quiz Server - Port 12345" | Get-NetFirewallProfile

# Eğer Public profile kapalıysa, kuralı güncelle
Set-NetFirewallRule -DisplayName "Quiz Server - Port 12345" -Profile Domain,Private,Public
```

## Adım 3: Client.py ile Bağlanma

Mac'te `client.py` çalıştırın:

1. **Server IP:** `10.51.113.149` (127.0.0.1 DEĞİL!)
2. **Port:** `12345`
3. **Username:** Benzersiz bir isim
4. **Connect** butonuna tıklayın

## Sorun Giderme

### "Connection timeout" hatası alıyorsanız:

1. **Mac'ten ping testi:**
   ```bash
   ping 10.51.113.149
   ```
   - Başarısızsa → Aynı ağda değilsiniz

2. **Mac'ten port testi:**
   ```bash
   python test_connection.py 10.51.113.149 12345
   ```
   - Başarısızsa → Firewall sorunu

3. **Windows'ta firewall kontrolü:**
   ```powershell
   Get-NetFirewallRule -DisplayName "Quiz Server - Port 12345"
   ```
   - Kural yoksa veya kapalıysa → Kural ekleyin

4. **Server çalışıyor mu kontrol:**
   - Windows'ta: `netstat -an | findstr :12345`
   - `LISTENING` görünmeli

### Mac ve Windows IP'leri farklı ağdaysa:

Örnek:
- Windows: `10.51.113.149` (10.51.113.x ağı)
- Mac: `192.168.1.50` (192.168.1.x ağı)

→ **Bu durumda bağlanamazsınız!** İkisi de aynı router'a bağlı olmalı.


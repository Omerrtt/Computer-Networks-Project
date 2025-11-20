# Windows Firewall - Port 12345 için Gelen Bağlantı Kuralı Ekleme
# Bu script'i yönetici olarak çalıştırın

# Gelen bağlantılar için kural ekle
New-NetFirewallRule -DisplayName "Quiz Server - Port 12345" `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort 12345 `
    -Action Allow `
    -Profile Any `
    -Description "Quiz Server uygulaması için gelen bağlantıları kabul eder"

Write-Host "Firewall kuralı başarıyla eklendi!" -ForegroundColor Green
Write-Host "Port 12345 artık gelen bağlantıları kabul edecek." -ForegroundColor Green


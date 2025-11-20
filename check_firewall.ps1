# Windows Firewall Durumunu Kontrol Etme Scripti
# Bu script port 12345'in firewall'da açık olup olmadığını kontrol eder

Write-Host "Windows Firewall Kontrolü" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan
Write-Host ""

$port = 12345

# Port için gelen kural var mı kontrol et
$inboundRule = Get-NetFirewallRule | Where-Object {
    $_.DisplayName -like "*Quiz Server*" -or 
    $_.DisplayName -like "*$port*"
} | Get-NetFirewallPortFilter | Where-Object {
    $_.LocalPort -eq $port -and $_.Protocol -eq "TCP"
}

if ($inboundRule) {
    Write-Host "✅ Port $port için firewall kuralı BULUNDU!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Kural detayları:"
    Get-NetFirewallRule | Where-Object {
        $_.DisplayName -like "*Quiz Server*" -or 
        $_.DisplayName -like "*$port*"
    } | Format-Table DisplayName, Enabled, Direction, Action -AutoSize
} else {
    Write-Host "❌ Port $port için firewall kuralı BULUNAMADI!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Firewall kuralı eklemek için şu komutu çalıştırın:" -ForegroundColor Yellow
    Write-Host "New-NetFirewallRule -DisplayName 'Quiz Server - Port $port' -Direction Inbound -Protocol TCP -LocalPort $port -Action Allow -Profile Any" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Veya firewall_setup.ps1 script'ini yönetici olarak çalıştırın." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Tüm gelen kuralları görmek için:" -ForegroundColor Cyan
Write-Host "Get-NetFirewallRule -Direction Inbound | Where-Object {$_.Enabled -eq $true} | Format-Table DisplayName, Enabled, Direction" -ForegroundColor Gray


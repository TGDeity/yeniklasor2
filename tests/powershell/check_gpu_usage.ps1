# GPU Kullanım Kontrol Scripti
Write-Host "=== GPU Kullanım Kontrol Scripti ===" -ForegroundColor Green

# Worker container loglarını kontrol et
Write-Host "`n1. Worker Container Logları:" -ForegroundColor Yellow
docker logs yeniklasr2-worker-1 --tail 50

Write-Host "`n2. GPU Durumu Kontrol:" -ForegroundColor Yellow
# NVIDIA GPU durumu (eğer varsa)
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
    Write-Host "NVIDIA GPU Durumu:" -ForegroundColor Cyan
    nvidia-smi
} else {
    Write-Host "NVIDIA GPU bulunamadı veya nvidia-smi yüklü değil" -ForegroundColor Red
}

Write-Host "`n3. Container GPU Erişimi:" -ForegroundColor Yellow
# Worker container'ın GPU erişimini kontrol et
docker exec yeniklasr2-worker-1 nvidia-smi 2>$null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Worker container GPU erişimi var" -ForegroundColor Green
} else {
    Write-Host "Worker container GPU erişimi yok" -ForegroundColor Red
}

Write-Host "`n4. Docker Compose GPU Konfigürasyonu:" -ForegroundColor Yellow
# docker-compose.yml'de GPU konfigürasyonunu kontrol et
Get-Content docker-compose.yml | Select-String -Pattern "gpu|nvidia|device" -Context 2

Write-Host "`n5. Son İşlenen Video Logları:" -ForegroundColor Yellow
# Belirli video ID'si için logları ara
$videoId = "432ac097-e2d9-41ec-ab02-31f96207cb3a"
Write-Host "Video ID: $videoId için loglar aranıyor..." -ForegroundColor Cyan
docker logs yeniklasr2-worker-1 2>&1 | Select-String -Pattern $videoId -Context 3

Write-Host "`n6. Whisper GPU Kullanım Logları:" -ForegroundColor Yellow
# Whisper GPU kullanım loglarını ara
docker logs yeniklasr2-worker-1 2>&1 | Select-String -Pattern "gpu|cuda|whisper|device" -Context 2

Write-Host "`n7. FFmpeg GPU Kullanım Logları:" -ForegroundColor Yellow
# FFmpeg GPU kullanım loglarını ara
docker logs yeniklasr2-worker-1 2>&1 | Select-String -Pattern "ffmpeg|hwaccel|gpu|nvenc|nvdec" -Context 2

Write-Host "`n8. Container Environment Variables:" -ForegroundColor Yellow
# Container environment variables'ları kontrol et
Write-Host "Worker container environment variables:" -ForegroundColor Cyan
docker exec yeniklasr2-worker-1 env | Select-String -Pattern "CUDA|GPU|DEVICE"

Write-Host "`n=== Kontrol Tamamlandı ===" -ForegroundColor Green 
# GPU FFmpeg Test Scripti (PowerShell 5.x uyumlu)
Write-Host "=== GPU FFmpeg Test Scripti ===" -ForegroundColor Green

# Test video dosyası var mı kontrol et
$testVideo = "uploads/test_video.mp4"
if (Test-Path $testVideo) {
    Write-Host "Test video bulundu: $testVideo" -ForegroundColor Green
} else {
    Write-Host "Test video bulunamadı: $testVideo" -ForegroundColor Red
    Write-Host "Lütfen önce bir test video yükleyin." -ForegroundColor Yellow
    exit 1
}

# API'ye test video yükle (multipart/form-data, PowerShell 5.x)
Write-Host "`n1. Test video yükleniyor..." -ForegroundColor Yellow
$uploadUrl = "http://localhost:8082/api/v1/upload"
$boundary = [System.Guid]::NewGuid().ToString()
$LF = "`r`n"

$fileBytes = [System.IO.File]::ReadAllBytes($testVideo)
$fileEnc = [System.Text.Encoding]::GetEncoding("ISO-8859-1").GetString($fileBytes)

$bodyLines = @(
    "--$boundary"
    'Content-Disposition: form-data; name="file"; filename="test_video.mp4"'
    "Content-Type: video/mp4$LF"
    $fileEnc
    "--$boundary"
    'Content-Disposition: form-data; name="target_language"'
    ""
    "tr"
    "--$boundary--$LF"
)
$body = [System.Text.Encoding]::GetEncoding("ISO-8859-1").GetBytes(($bodyLines -join $LF))

try {
    $response = Invoke-WebRequest -Uri $uploadUrl -Method Post -ContentType "multipart/form-data; boundary=$boundary" -Body $body
    $json = $response.Content | ConvertFrom-Json
    $videoId = $json.video_id
    $taskId = $json.task_id
    Write-Host "Video yüklendi! Video ID: $videoId, Task ID: $taskId" -ForegroundColor Green

    # Status kontrolü
    Write-Host "`n2. İşlem durumu kontrol ediliyor..." -ForegroundColor Yellow
    $statusUrl = "http://localhost:8082/api/v1/status/$videoId"
    $maxWait = 60  # 60 saniye bekle
    $waitTime = 0
    while ($waitTime -lt $maxWait) {
        try {
            $statusResp = Invoke-WebRequest -Uri $statusUrl -Method Get
            $status = $statusResp.Content | ConvertFrom-Json
            Write-Host "Durum: $($status.status), İlerleme: $($status.progress)%" -ForegroundColor Cyan
            if ($status.status -eq "completed") {
                Write-Host "`n✅ Video başarıyla işlendi!" -ForegroundColor Green
                Write-Host "Sonuç: $($status.result | ConvertTo-Json -Depth 3)" -ForegroundColor Green
                break
            } elseif ($status.status -eq "failed") {
                Write-Host "`n❌ Video işleme başarısız!" -ForegroundColor Red
                break
            }
            Start-Sleep -Seconds 3
            $waitTime += 3
        } catch {
            Write-Host "Status kontrol hatası: $($_.Exception.Message)" -ForegroundColor Red
            break
        }
    }
    if ($waitTime -ge $maxWait) {
        Write-Host "`n⏰ Timeout: Video işleme tamamlanamadı" -ForegroundColor Yellow
    }
} catch {
    Write-Host "Video yükleme hatası: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n3. Worker loglarını kontrol ediliyor..." -ForegroundColor Yellow
docker logs yeniklasr2-worker-1 --tail 40 | Select-String -Pattern "GPU|nvenc|ffmpeg|completed|success" -Context 2

Write-Host "`n=== Test Tamamlandı ===" -ForegroundColor Green 
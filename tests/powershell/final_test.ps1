# Final test script
Write-Host "Testing video upload and processing..." -ForegroundColor Yellow

try {
    # Use existing file
    $videoPath = "uploads/ffe27801-5e05-4cb4-8f00-1342ed39f151_test.mp4"
    
    # Create form data
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    $bodyLines = (
        "--$boundary",
        "Content-Disposition: form-data; name=`"target_language`"",
        "",
        "tr",
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"test.mp4`"",
        "Content-Type: video/mp4",
        "",
        [System.IO.File]::ReadAllBytes($videoPath),
        "--$boundary--"
    ) -join $LF
    
    $headers = @{
        "Content-Type" = "multipart/form-data; boundary=$boundary"
    }
    
    $response = Invoke-RestMethod -Uri "http://localhost:8082/api/v1/upload/" -Method Post -Body $bodyLines -Headers $headers -TimeoutSec 60
    
    Write-Host "Upload successful!" -ForegroundColor Green
    Write-Host "Video ID: $($response.video_id)" -ForegroundColor Cyan
    
    # Monitor for 2 minutes
    $startTime = Get-Date
    while ((Get-Date) - $startTime).TotalSeconds -lt 120) {
        Start-Sleep -Seconds 10
        
        $status = Invoke-RestMethod -Uri "http://localhost:8082/api/v1/status/$($response.video_id)" -Method Get -TimeoutSec 10
        Write-Host "Status: $($status.status)" -ForegroundColor Cyan
        
        if ($status.status -eq "completed") {
            Write-Host "✅ Processing completed!" -ForegroundColor Green
            break
        }
        elseif ($status.status -eq "failed") {
            Write-Host "❌ Processing failed: $($status.error)" -ForegroundColor Red
            break
        }
    }
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
} 
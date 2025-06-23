# Quick test with existing file
Write-Host "Quick test..." -ForegroundColor Yellow

try {
    # Use existing file
    $videoPath = "uploads/test_copy.mp4"
    
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
    
    # Check status after 10 seconds
    Start-Sleep -Seconds 10
    $status = Invoke-RestMethod -Uri "http://localhost:8082/api/v1/status/$($response.video_id)" -Method Get
    Write-Host "Status: $($status.status)" -ForegroundColor Cyan
    
    if ($status.error) {
        Write-Host "Error: $($status.error)" -ForegroundColor Red
    }
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
} 
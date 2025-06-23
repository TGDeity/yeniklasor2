# Test new video upload
Write-Host "Testing new video upload..." -ForegroundColor Yellow

try {
    # Use the new test video
    $videoPath = "uploads/testen.mp4"
    
    # Simple curl command
    $curlCmd = "curl.exe -X POST `"http://localhost:8082/api/v1/upload`" -H `"accept: application/json`" -H `"Content-Type: multipart/form-data`" -F `"file=@$videoPath`" -F `"target_language=tr`""
    
    Write-Host "Running: $curlCmd" -ForegroundColor Cyan
    $response = Invoke-Expression $curlCmd
    
    Write-Host "Response: $response" -ForegroundColor Green
    
    # Parse response to get video ID
    if ($response -match '"video_id":"([^"]+)"') {
        $videoId = $matches[1]
        Write-Host "Video ID: $videoId" -ForegroundColor Cyan
        
        # Monitor status
        Start-Sleep -Seconds 5
        $status = Invoke-RestMethod -Uri "http://localhost:8082/api/v1/status/$videoId" -Method Get
        Write-Host "Status: $($status.status)" -ForegroundColor Cyan
    }
}
catch {
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
} 
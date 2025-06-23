# Test Video Upload Script
Write-Host "=== Video Upload Test ===" -ForegroundColor Green

# Check if test video exists
$testVideoPath = "uploads\test_video.mp4"
if (-not (Test-Path $testVideoPath)) {
    Write-Host "Test video not found at $testVideoPath" -ForegroundColor Red
    Write-Host "Please ensure test_video.mp4 exists in the uploads folder" -ForegroundColor Yellow
    exit 1
}

Write-Host "Found test video: $testVideoPath" -ForegroundColor Green

# API endpoint
$apiUrl = "http://localhost:8082/api/v1/upload"

Write-Host "Uploading video to: $apiUrl" -ForegroundColor Cyan

try {
    # Create multipart form data
    $boundary = [System.Guid]::NewGuid().ToString()
    $LF = "`r`n"
    
    $bodyLines = @(
        "--$boundary",
        "Content-Disposition: form-data; name=`"file`"; filename=`"test_video.mp4`"",
        "Content-Type: video/mp4",
        "",
        [System.IO.File]::ReadAllBytes($testVideoPath),
        "--$boundary",
        "Content-Disposition: form-data; name=`"language`"",
        "",
        "en",
        "--$boundary--"
    )
    
    $body = $bodyLines -join $LF
    
    # Make the request
    $response = Invoke-RestMethod -Uri $apiUrl -Method POST -Body $body -ContentType "multipart/form-data; boundary=$boundary" -TimeoutSec 30
    
    Write-Host "Upload successful!" -ForegroundColor Green
    Write-Host "Response: $($response | ConvertTo-Json -Depth 3)" -ForegroundColor Cyan
    
    # Extract task ID if available
    if ($response.task_id) {
        Write-Host "Task ID: $($response.task_id)" -ForegroundColor Yellow
        Write-Host "You can check status at: http://localhost:8082/api/v1/status/$($response.task_id)" -ForegroundColor Yellow
        Write-Host "Or view in admin panel: http://localhost:8181" -ForegroundColor Yellow
    }
    
} catch {
    Write-Host "Upload failed!" -ForegroundColor Red
    Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
    
    if ($_.Exception.Response) {
        $statusCode = $_.Exception.Response.StatusCode
        $statusDescription = $_.Exception.Response.StatusDescription
        Write-Host "HTTP Status: $statusCode - $statusDescription" -ForegroundColor Red
        
        # Try to read response body
        try {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            Write-Host "Response Body: $responseBody" -ForegroundColor Red
        } catch {
            Write-Host "Could not read response body" -ForegroundColor Yellow
        }
    }
}

Write-Host "=== Test Complete ===" -ForegroundColor Green 
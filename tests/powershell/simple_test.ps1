# Simple test - copy existing file and test
$sourceFile = "uploads/ffe27801-5e05-4cb4-8f00-1342ed39f151_test.mp4"
$testFile = "uploads/test_video.mp4"

# Copy existing file
Copy-Item $sourceFile $testFile

Write-Host "Testing with existing file..." -ForegroundColor Yellow

# Use curl for upload (more reliable)
$curlCommand = @"
curl -X POST "http://localhost:8082/api/v1/upload" `
  -H "accept: application/json" `
  -H "Content-Type: multipart/form-data" `
  -F "file=@$testFile" `
  -F "target_language=tr"
"@

Write-Host "Running: $curlCommand" -ForegroundColor Cyan
Invoke-Expression $curlCommand 
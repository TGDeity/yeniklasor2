#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Debug script for video processing issues on Windows
.DESCRIPTION
    This script checks system resources, Docker services, and video processing status
#>

param(
    [string]$ApiUrl = "http://localhost:8082"
)

Write-Host "🌍 Video Processing API - Windows Debug Check" -ForegroundColor Cyan
Write-Host "=" * 50 -ForegroundColor Cyan

# Function to check system resources
function Check-SystemResources {
    Write-Host "`n📊 System Resources:" -ForegroundColor Yellow
    
    try {
        $cpu = Get-Counter "\Processor(_Total)\% Processor Time" -SampleInterval 1 -MaxSamples 1
        $memory = Get-Counter "\Memory\Available MBytes" -SampleInterval 1 -MaxSamples 1
        $disk = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
        
        Write-Host "CPU Usage: $($cpu.CounterSamples[0].CookedValue.ToString('F1'))%" -ForegroundColor Green
        Write-Host "Available Memory: $($memory.CounterSamples[0].CookedValue.ToString('F0')) MB" -ForegroundColor Green
        Write-Host "Free Disk Space: $([math]::Round($disk.FreeSpace / 1GB, 2)) GB" -ForegroundColor Green
    }
    catch {
        Write-Host "Could not get system info: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to check Docker services
function Check-DockerServices {
    Write-Host "`n🐳 Docker Services:" -ForegroundColor Yellow
    
    try {
        $services = docker-compose ps
        Write-Host $services -ForegroundColor Green
    }
    catch {
        Write-Host "Could not check Docker services: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to check API health
function Check-ApiHealth {
    Write-Host "`n🔌 API Health Check:" -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri "$ApiUrl/api/v1/upload/health" -Method Get -TimeoutSec 10
        Write-Host "API Status: Healthy" -ForegroundColor Green
        Write-Host "Upload Directory: $($response.upload_dir)" -ForegroundColor Green
        Write-Host "Supported Languages: $($response.supported_languages_count)" -ForegroundColor Green
    }
    catch {
        Write-Host "API Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to check supported languages
function Check-SupportedLanguages {
    Write-Host "`n🌐 Supported Languages:" -ForegroundColor Yellow
    
    try {
        $response = Invoke-RestMethod -Uri "$ApiUrl/api/v1/upload/languages" -Method Get -TimeoutSec 10
        Write-Host "Total Languages: $($response.count)" -ForegroundColor Green
        
        $popularLangs = @('tr', 'es', 'fr', 'de', 'it', 'pt', 'ru', 'ja', 'ko', 'zh')
        foreach ($lang in $popularLangs) {
            if ($response.languages.ContainsKey($lang)) {
                Write-Host "  $lang`: $($response.languages[$lang])" -ForegroundColor Cyan
            }
        }
    }
    catch {
        Write-Host "Could not get languages: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to check video files
function Check-VideoFiles {
    Write-Host "`n🎬 Video Files:" -ForegroundColor Yellow
    
    $uploadDir = "uploads"
    if (Test-Path $uploadDir) {
        $files = Get-ChildItem -Path $uploadDir -File
        Write-Host "Found $($files.Count) files in uploads directory" -ForegroundColor Green
        foreach ($file in $files) {
            $sizeMB = [math]::Round($file.Length / 1MB, 2)
            Write-Host "  $($file.Name): $sizeMB MB" -ForegroundColor Cyan
        }
    }
    else {
        Write-Host "Uploads directory does not exist" -ForegroundColor Yellow
    }
}

# Function to check status files
function Check-StatusFiles {
    Write-Host "`n📋 Status Files:" -ForegroundColor Yellow
    
    $statusDir = "status"
    if (Test-Path $statusDir) {
        $files = Get-ChildItem -Path $statusDir -Filter "*.json" -File
        Write-Host "Found $($files.Count) status files" -ForegroundColor Green
        foreach ($file in $files) {
            try {
                $content = Get-Content $file.FullName | ConvertFrom-Json
                Write-Host "  $($file.BaseName): $($content.status)" -ForegroundColor Cyan
            }
            catch {
                Write-Host "  $($file.BaseName): Error reading file" -ForegroundColor Red
            }
        }
    }
    else {
        Write-Host "Status directory does not exist" -ForegroundColor Yellow
    }
}

# Function to check logs
function Check-Logs {
    Write-Host "`n📝 Recent Logs:" -ForegroundColor Yellow
    
    $logDir = "logs"
    if (Test-Path $logDir) {
        $logFiles = Get-ChildItem -Path $logDir -Filter "*.log" -File | Sort-Object LastWriteTime -Descending
        foreach ($file in $logFiles | Select-Object -First 3) {
            Write-Host "Recent logs from $($file.Name):" -ForegroundColor Green
            try {
                $lines = Get-Content $file.FullName -Tail 5
                foreach ($line in $lines) {
                    Write-Host "  $line" -ForegroundColor Gray
                }
            }
            catch {
                Write-Host "  Could not read log file" -ForegroundColor Red
            }
        }
    }
    else {
        Write-Host "Logs directory does not exist" -ForegroundColor Yellow
    }
}

# Main execution
try {
    Check-SystemResources
    Check-DockerServices
    Check-ApiHealth
    Check-SupportedLanguages
    Check-VideoFiles
    Check-StatusFiles
    Check-Logs
    
    Write-Host "`n✅ Debug check completed!" -ForegroundColor Green
}
catch {
    Write-Host "`n❌ Error during debug check: $($_.Exception.Message)" -ForegroundColor Red
} 
#!/usr/bin/env powershell
# Script to update the installed 3ds Max submitter files with the latest source code
# This is much faster than rebuilding and reinstalling the entire installer during development

param(
    [string]$InstallPath = "C:\Users\RDP\DeadlineCloudFor3dsMaxSubmitter\scripts\deadline",
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

# Source and destination paths
$SourceRoot = "src\deadline"
$DestinationRoot = $InstallPath

Write-Host "=== 3ds Max Submitter File Updater ===" -ForegroundColor Green
Write-Host "Source: $SourceRoot" -ForegroundColor Cyan
Write-Host "Destination: $DestinationRoot" -ForegroundColor Cyan
Write-Host ""

# Check if source directory exists
if (-not (Test-Path $SourceRoot)) {
    Write-Error "Source directory not found: $SourceRoot"
    Write-Host "Make sure you're running this script from the deadline-cloud-for-3ds-max root directory"
    exit 1
}

# Check if destination directory exists
if (-not (Test-Path $DestinationRoot)) {
    Write-Error "Destination directory not found: $DestinationRoot"
    Write-Host "Make sure the 3ds Max submitter is installed at: $InstallPath"
    exit 1
}

# Function to copy files with logging
function Copy-FilesWithLogging {
    param(
        [string]$Source,
        [string]$Destination,
        [string]$Description
    )
    
    Write-Host "Updating $Description..." -ForegroundColor Yellow
    
    if (-not (Test-Path $Source)) {
        Write-Warning "Source not found: $Source"
        return
    }
    
    # Create destination directory if it doesn't exist
    $DestDir = Split-Path $Destination -Parent
    if (-not (Test-Path $DestDir)) {
        New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
        if ($Verbose) { Write-Host "  Created directory: $DestDir" -ForegroundColor Gray }
    }
    
    try {
        # Copy the entire directory tree
        Copy-Item -Path $Source -Destination $Destination -Recurse -Force
        Write-Host "  ✓ Updated: $Description" -ForegroundColor Green
        
        if ($Verbose) {
            $FileCount = (Get-ChildItem -Path $Destination -Recurse -File | Measure-Object).Count
            Write-Host "    Files copied: $FileCount" -ForegroundColor Gray
        }
    }
    catch {
        Write-Error "Failed to copy $Description`: $_"
    }
}

# Update max_submitter files
Write-Host "1. Updating max_submitter files..." -ForegroundColor Magenta
Copy-FilesWithLogging -Source "$SourceRoot\max_submitter" -Destination "$DestinationRoot\max_submitter" -Description "max_submitter module"

# Update max_shared files
Write-Host "2. Updating max_shared files..." -ForegroundColor Magenta
Copy-FilesWithLogging -Source "$SourceRoot\max_shared" -Destination "$DestinationRoot\max_shared" -Description "max_shared module"

Write-Host ""
Write-Host "=== Update Complete ===" -ForegroundColor Green
Write-Host "The installed 3ds Max submitter files have been updated with your latest changes." -ForegroundColor White
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Restart 3ds Max if it is currently running" -ForegroundColor White
Write-Host "2. Test the submitter to verify your changes work correctly" -ForegroundColor White
Write-Host ""

# Optional: Show what files were updated
if ($Verbose) {
    Write-Host "Updated files:" -ForegroundColor Cyan
    Get-ChildItem -Path "$DestinationRoot\max_submitter" -Recurse -File | ForEach-Object {
        Write-Host "  $($_.FullName)" -ForegroundColor Gray
    }
    Get-ChildItem -Path "$DestinationRoot\max_shared" -Recurse -File | ForEach-Object {
        Write-Host "  $($_.FullName)" -ForegroundColor Gray
    }
}
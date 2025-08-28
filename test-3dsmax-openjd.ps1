# 3ds Max Adaptor Testing Script
# Tests the deadline-cloud-for-3ds-max adaptor directly without worker agent setup

param(
    [string]$WheelPath = "dist\deadline_cloud_for_3ds_max-0.1.5.post5+g9c00ceba7-py3-none-any.whl",
    [string]$MaxVersion = "2026",
    [string]$JobBundleDir = "2025-08-22-04-3dsMax-CloudyRoom-VolumeFog",
    [switch]$SkipInstall,
    [switch]$Verbose,
    [switch]$Help
)

# Show help if requested
if ($Help) {
    Write-Host "=== 3ds Max Adaptor Testing Script Help ===" -ForegroundColor Green
    Write-Host ""
    Write-Host "DESCRIPTION:" -ForegroundColor Yellow
    Write-Host "  Tests the deadline-cloud-for-3ds-max adaptor directly without worker agent setup"
    Write-Host ""
    Write-Host "PREREQUISITES:" -ForegroundColor Yellow
    Write-Host "  Install PowerShell YAML module for proper parameter parsing:"
    Write-Host "  Install-Module powershell-yaml -Force" -ForegroundColor Cyan
    Write-Host ""
    exit 0
}

# Configuration
$MaxPythonPath = "C:\Program Files\Autodesk\3ds Max $MaxVersion\Python\python.exe"
$LogDir = "C:\Users\$env:USERNAME\AppData\Local\Autodesk\3dsMax\$MaxVersion - 64bit\ENU\Network"

Write-Host "=== 3ds Max Adaptor Testing Script ===" -ForegroundColor Green
Write-Host "Wheel: $WheelPath" -ForegroundColor Cyan
Write-Host "Max Version: $MaxVersion" -ForegroundColor Cyan
Write-Host "Job Bundle: $JobBundleDir" -ForegroundColor Cyan

# Function to check prerequisites
function Test-Prerequisites {
    Write-Host "`n--- Checking Prerequisites ---" -ForegroundColor Yellow
    
    # Check if 3ds Max Python exists
    if (-not (Test-Path $MaxPythonPath)) {
        Write-Error "3ds Max Python not found at: $MaxPythonPath"
        Write-Host "Please ensure 3ds Max $MaxVersion is installed" -ForegroundColor Red
        return $false
    }
    Write-Host "3ds Max Python found" -ForegroundColor Green
    
    # Check if wheel file exists
    if (-not (Test-Path $WheelPath)) {
        Write-Error "Wheel file not found at: $WheelPath"
        return $false
    }
    Write-Host "Wheel file found" -ForegroundColor Green
    
    # Check if job bundle exists
    if (-not (Test-Path $JobBundleDir)) {
        Write-Error "Job bundle directory not found: $JobBundleDir"
        return $false
    }
    Write-Host "Job bundle directory found" -ForegroundColor Green
    
    return $true
}

# Function to setup environment variables
function Setup-Environment {
    Write-Host "`n--- Setting Up Environment ---" -ForegroundColor Yellow
    
    $maxPythonDir = Split-Path $MaxPythonPath -Parent
    $pythonScriptsDir = "C:\Users\$env:USERNAME\AppData\Roaming\Python\Python311\Scripts"
    $repoPath = Get-Location
    $maxSubmitterPath = "$repoPath\src\deadline\max_submitter"
    
    # Set PATH with 3ds Max Python and executable FIRST (highest priority)
    $maxExecutableDir = "C:\Program Files\Autodesk\3ds Max $MaxVersion"
    Write-Host "Setting up PATH with 3ds Max priority..." -ForegroundColor Gray
    $env:PATH = "$maxPythonDir;$maxExecutableDir;$pythonScriptsDir;$env:PATH"
    Write-Host "Updated PATH to include:" -ForegroundColor Green
    Write-Host "  - 3ds Max Python: $maxPythonDir" -ForegroundColor Green
    Write-Host "  - 3ds Max Executable: $maxExecutableDir" -ForegroundColor Green
    
    # Set PYTHONPATH with 3ds Max Python FIRST
    $env:PYTHONPATH = "$maxPythonDir;$repoPath\src;$maxSubmitterPath"
    Write-Host "Set PYTHONPATH: $env:PYTHONPATH" -ForegroundColor Green
    
    # Set ADSK_3DSMAX_SCRIPTS_ADDON_DIR
    $env:ADSK_3DSMAX_SCRIPTS_ADDON_DIR = $maxSubmitterPath
    Write-Host "Set ADSK_3DSMAX_SCRIPTS_ADDON_DIR: $maxSubmitterPath" -ForegroundColor Green
    
    # Verify Python priority - CRITICAL CHECK
    Write-Host "`n--- Verifying Python Priority ---" -ForegroundColor Yellow
    try {
        $pythonPath = (Get-Command python -ErrorAction Stop).Source
        $pythonVersion = & python --version 2>&1
        
        Write-Host "Expected 3ds Max Python: $MaxPythonPath" -ForegroundColor Cyan
        Write-Host "Actual Default Python:   $pythonPath" -ForegroundColor Cyan
        Write-Host "Version: $pythonVersion" -ForegroundColor Cyan
        
        # Check if the paths match (normalize for comparison)
        $expectedNorm = $MaxPythonPath.ToLower().Replace('\', '/')
        $actualNorm = $pythonPath.ToLower().Replace('\', '/')
        
        if ($actualNorm -eq $expectedNorm) {
            Write-Host "SUCCESS: 3ds Max Python is now the default Python" -ForegroundColor Green
        } else {
            Write-Host "CRITICAL ERROR: Wrong Python interpreter detected!" -ForegroundColor Red
            Write-Host "Expected: $MaxPythonPath" -ForegroundColor Red
            Write-Host "Got:      $pythonPath" -ForegroundColor Red
            Write-Host ""
            Write-Host "This will cause module import failures. Exiting..." -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "FAILED: Could not verify Python priority" -ForegroundColor Red
        Write-Host "Error: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
    
    Write-Host "Note: Environment changes are temporary for this session only" -ForegroundColor Yellow
    return $true
}

# Function to install the adaptor
function Install-Adaptor {
    Write-Host "`n--- Installing Adaptor ---" -ForegroundColor Yellow
    
    Write-Host "Running: $MaxPythonPath -m pip install $WheelPath --force-reinstall" -ForegroundColor Cyan
    
    try {
        & $MaxPythonPath -m pip install $WheelPath --force-reinstall
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Adaptor installed successfully" -ForegroundColor Green
            return $true
        } else {
            Write-Error "Failed to install adaptor (exit code: $LASTEXITCODE)"
            return $false
        }
    } catch {
        Write-Error "Exception during installation: $($_.Exception.Message)"
        return $false
    }
}

# Function to build test command from job bundle
function Build-TestCommand {
    Write-Host "`n--- Building Test Command ---" -ForegroundColor Yellow
    
    # Read parameter values
    $paramFile = Join-Path $JobBundleDir "parameter_values.yaml"
    if (-not (Test-Path $paramFile)) {
        Write-Error "Parameter values file not found: $paramFile"
        return $null
    }
    
    # Import PowerShell-Yaml module for proper YAML parsing
    try {
        Import-Module powershell-yaml -ErrorAction Stop
        Write-Host "Using PowerShell-Yaml module for parsing" -ForegroundColor Gray
    } catch {
        Write-Error "PowerShell-Yaml module is required for YAML parsing."
        Write-Host "Please install it with: Install-Module powershell-yaml -Force" -ForegroundColor Yellow
        return $null
    }
    
    # Parse YAML properly
    $paramContent = Get-Content $paramFile -Raw
    $yamlData = ConvertFrom-Yaml $paramContent
    
    # Extract values from parsed YAML
    $getValue = { param($name) 
        $param = $yamlData.parameterValues | Where-Object { $_.name -eq $name }
        if ($param) { 
            return $param.value 
        } else { 
            return "" 
        }
    }
    
    $sceneFile = & $getValue "MaxSceneFile"
    $frames = & $getValue "Frames"
    $outputPath = & $getValue "OutputFilePath"
    $outputFormat = & $getValue "OutputFileFormat"
    $imageWidth = & $getValue "ImageWidth"
    $imageHeight = & $getValue "ImageHeight"
    
    # Set defaults if values are empty
    $frames = if ([string]::IsNullOrEmpty($frames)) { "0" } else { $frames }
    $outputFormat = if ([string]::IsNullOrEmpty($outputFormat)) { ".jpg" } else { $outputFormat }
    $imageWidth = if ([string]::IsNullOrEmpty($imageWidth)) { "320" } else { $imageWidth }
    $imageHeight = if ([string]::IsNullOrEmpty($imageHeight)) { "240" } else { $imageHeight }
    
    # Build init data JSON
    $initData = @{
        scene_file = $sceneFile
        renderer = "V_Ray_GPU_7_Hotfix_2"
        state_set = "State01"
        output_file_name = "State01_CloudyRoom-VolumeFog_###"
        output_file_path = $outputPath
        output_file_format = $outputFormat
        image_width = [int]$imageWidth
        image_height = [int]$imageHeight
    } | ConvertTo-Json -Compress
    
    # Build run data JSON
    $runData = @{
        frame = [int]$frames.Split(',')[0].Split('-')[0]  # Take first frame
        camera = "Camera01"
    } | ConvertTo-Json -Compress
    
    # Write JSON data to temporary files to avoid command line escaping issues
    $tempDir = [System.IO.Path]::GetTempPath()
    $initDataFile = Join-Path $tempDir "3dsmax-init-data.json"
    $runDataFile = Join-Path $tempDir "3dsmax-run-data.json"
    
    # Write JSON files
    $initData | Out-File -FilePath $initDataFile -Encoding UTF8
    $runData | Out-File -FilePath $runDataFile -Encoding UTF8
    
    # Use the 3dsmax-openjd wrapper script with file references
    $testCommand = "3dsmax-openjd run --init-data file://$initDataFile --run-data file://$runDataFile"
    
    Write-Host "Scene File: $sceneFile" -ForegroundColor Cyan
    Write-Host "Frame: $($runData | ConvertFrom-Json | Select-Object -ExpandProperty frame)" -ForegroundColor Cyan
    Write-Host "Output: $outputPath" -ForegroundColor Cyan
    Write-Host "`nTest Command:" -ForegroundColor Yellow
    Write-Host $testCommand -ForegroundColor White
    
    return $testCommand
}

# Function to run the test
function Run-Test {
    param([string]$TestCommand)
    
    Write-Host "`n--- Running Test ---" -ForegroundColor Yellow
    Write-Host "Command: $TestCommand" -ForegroundColor Cyan
    
    $startTime = Get-Date
    Write-Host "Started at: $startTime" -ForegroundColor Gray
    
    try {
        # Run the command and capture output
        $output = cmd /c $TestCommand 2>&1
        $endTime = Get-Date
        $duration = $endTime - $startTime
        
        Write-Host "`nTest completed in: $($duration.TotalSeconds) seconds" -ForegroundColor Gray
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "Test completed successfully!" -ForegroundColor Green
            if ($Verbose) {
                Write-Host "`nOutput:" -ForegroundColor Gray
                $output | ForEach-Object { Write-Host $_ -ForegroundColor Gray }
            }
        } else {
            Write-Host "Test failed (exit code: $LASTEXITCODE)" -ForegroundColor Red
            Write-Host "`nOutput:" -ForegroundColor Gray
            $output | ForEach-Object { Write-Host $_ -ForegroundColor Red }
        }
        
        return $LASTEXITCODE -eq 0
    } catch {
        Write-Error "Exception during test execution: $($_.Exception.Message)"
        return $false
    }
}

# Function to check logs
function Check-Logs {
    Write-Host "`n--- Checking Logs ---" -ForegroundColor Yellow
    
    if (Test-Path $LogDir) {
        $logFiles = Get-ChildItem $LogDir -Filter "*.log" | Sort-Object LastWriteTime -Descending | Select-Object -First 3
        if ($logFiles) {
            Write-Host "Recent log files in $LogDir" -ForegroundColor Cyan
            foreach ($log in $logFiles) {
                Write-Host "  $($log.Name) - $($log.LastWriteTime)" -ForegroundColor Gray
            }
            Write-Host "`nTo view latest log: Get-Content '$($logFiles[0].FullName)' -Tail 20" -ForegroundColor Yellow
        } else {
            Write-Host "No log files found in $LogDir" -ForegroundColor Gray
        }
    } else {
        Write-Host "Log directory not found: $LogDir" -ForegroundColor Gray
    }
}

# Main execution
try {
    # Check prerequisites
    if (-not (Test-Prerequisites)) {
        exit 1
    }
    
    # Setup environment variables
    if (-not (Setup-Environment)) {
        Write-Host "`nEnvironment setup failed. Cannot continue with wrong Python interpreter." -ForegroundColor Red
        exit 1
    }
    
    # Install adaptor (unless skipped)
    if (-not $SkipInstall) {
        if (-not (Install-Adaptor)) {
            exit 1
        }
    } else {
        Write-Host "`n--- Skipping Installation ---" -ForegroundColor Yellow
    }
    
    # Build test command
    $testCommand = Build-TestCommand
    if (-not $testCommand) {
        exit 1
    }
    
    # Run test
    $success = Run-Test -TestCommand $testCommand
    
    # Check logs regardless of success/failure
    Check-Logs
    
    if ($success) {
        Write-Host "`nTest completed successfully!" -ForegroundColor Green
        exit 0
    } else {
        Write-Host "`nTest failed. Check the output above and logs for details." -ForegroundColor Red
        exit 1
    }
    
} catch {
    Write-Error "Unexpected error: $($_.Exception.Message)"
    exit 1
}
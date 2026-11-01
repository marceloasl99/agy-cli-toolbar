# Antigravity CLI Toolbar (agy-cli-toolbar) Installer for Windows
$ErrorActionPreference = "Stop"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "   Antigravity CLI Toolbar Installer (Windows)" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

$userProfile = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)
$customDir = Join-Path $userProfile ".antigravity-custom"
$targetScript = Join-Path $customDir "statusline.py"
$targetConfig = Join-Path $customDir "config.json"
$settingsPath = Join-Path $userProfile ".gemini\antigravity-cli\settings.json"

# 1. Create target directory
if (!(Test-Path $customDir)) {
    New-Item -ItemType Directory -Path $customDir -Force | Out-Null
    Write-Host "[✓] Created custom directory: $customDir" -ForegroundColor Green
}

# 2. Copy script
$sourceScript = Join-Path $PSScriptRoot "statusline.py"
if (Test-Path $sourceScript) {
    Copy-Item $sourceScript $targetScript -Force
    Write-Host "[✓] Installed statusline script: $targetScript" -ForegroundColor Green
} else {
    Write-Host "[!] Could not find local statusline.py, downloading..." -ForegroundColor Yellow
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/marceloasl99/agy-cli-toolbar/main/statusline.py" -OutFile $targetScript
    Write-Host "[✓] Downloaded and installed statusline.py" -ForegroundColor Green
}

# 3. Create default config if not existing
if (!(Test-Path $targetConfig)) {
    $sourceConfig = Join-Path $PSScriptRoot "config.example.json"
    if (Test-Path $sourceConfig) {
        Copy-Item $sourceConfig $targetConfig -Force
    } else {
        Invoke-WebRequest -Uri "https://raw.githubusercontent.com/marceloasl99/agy-cli-toolbar/main/config.example.json" -OutFile $targetConfig
    }
    Write-Host "[✓] Created configuration file: $targetConfig" -ForegroundColor Green
}

# 4. Configure settings.json
if (Test-Path $settingsPath) {
    Write-Host "[*] Checking Antigravity CLI settings..." -ForegroundColor Cyan
    try {
        $settingsRaw = Get-Content $settingsPath -Raw -Encoding UTF8
        $settings = $settingsRaw | ConvertFrom-Json

        $escapedPath = $targetScript.Replace("\", "\\")
        $statusLineConfig = [PSCustomObject]@{
            type = "command"
            command = "python $targetScript"
            padding = 0
            stack_with_default = $false
            enabled = $true
        }

        # Backup settings
        $backupPath = "$settingsPath.bak"
        Copy-Item $settingsPath $backupPath -Force
        Write-Host "[✓] Created backup: $backupPath" -ForegroundColor Green

        $settings | Add-Member -MemberType NoteProperty -Name "statusLine" -Value $statusLineConfig -Force
        $updatedJson = $settings | ConvertTo-Json -Depth 10
        [System.IO.File]::WriteAllText($settingsPath, $updatedJson, [System.Text.Encoding]::UTF8)
        Write-Host "[✓] Updated settings.json with custom statusLine" -ForegroundColor Green
    } catch {
        Write-Host "[!] Error updating settings.json automatically: $_" -ForegroundColor Yellow
    }
}

Write-Host "`nInstallation completed successfully!" -ForegroundColor Green
Write-Host "To test right now in your open Antigravity CLI session, run:" -ForegroundColor White
Write-Host "/statusline python $targetScript`n" -ForegroundColor Yellow

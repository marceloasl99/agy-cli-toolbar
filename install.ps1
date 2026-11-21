# Antigravity CLI Toolbar (agy-cli-toolbar) Installer for Windows
$ErrorActionPreference = "Stop"

Write-Host "==============================================" -ForegroundColor Cyan
Write-Host "   Antigravity CLI Toolbar Installer (Windows)" -ForegroundColor Cyan
Write-Host "==============================================" -ForegroundColor Cyan

$userProfile = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::UserProfile)
$customDir = Join-Path $userProfile ".antigravity-custom"
$targetScript = Join-Path $customDir "statusline.py"
$targetConfig = Join-Path $customDir "config.json"
$targetProfileMgr = Join-Path $customDir "profile_manager.py"
$targetOAuth = Join-Path $customDir "oauth_auth.py"
$settingsPath = Join-Path $userProfile ".gemini\antigravity-cli\settings.json"
$agyBinDir = Join-Path $userProfile "AppData\Local\agy\bin"

# 1. Create target directory
if (!(Test-Path $customDir)) {
    New-Item -ItemType Directory -Path $customDir -Force | Out-Null
    Write-Host "[✓] Created custom directory: $customDir" -ForegroundColor Green
}

# 2. Copy scripts
$scripts = @("statusline.py", "profile_manager.py", "oauth_auth.py", "tray_app.pyw")
foreach ($s in $scripts) {
    $sourceScript = Join-Path $PSScriptRoot $s
    $destScript = Join-Path $customDir $s
    if (Test-Path $sourceScript) {
        Copy-Item $sourceScript $destScript -Force
        Write-Host "[✓] Installed: $destScript" -ForegroundColor Green
    } else {
        Invoke-WebRequest -Uri "https://raw.githubusercontent.com/marceloasl99/agy-cli-toolbar/main/$s" -OutFile $destScript
        Write-Host "[✓] Downloaded and installed: $s" -ForegroundColor Green
    }
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

# 4. Install command wrappers
if (Test-Path $agyBinDir) {
    $wrappers = @("agy-profile.cmd", "agy-profile.ps1", "agy-tray.cmd")
    foreach ($w in $wrappers) {
        $sourceW = Join-Path $PSScriptRoot $w
        if (Test-Path $sourceW) {
            Copy-Item $sourceW (Join-Path $agyBinDir $w) -Force
        }
    }
    Write-Host "[✓] Installed agy-profile and agy-tray CLI commands to: $agyBinDir" -ForegroundColor Green
}

# 5. Configure settings.json
if (Test-Path $settingsPath) {
    Write-Host "[*] Checking Antigravity CLI settings..." -ForegroundColor Cyan
    try {
        $settingsRaw = Get-Content $settingsPath -Raw -Encoding UTF8
        $settings = $settingsRaw | ConvertFrom-Json

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

# 6. Create Desktop Shortcut
try {
    $shortcutScript = Join-Path $PSScriptRoot "create_shortcut.py"
    if (Test-Path $shortcutScript) {
        python $shortcutScript | Out-Null
        Write-Host "[✓] Created desktop shortcut: Antigravity Quotas" -ForegroundColor Green
    }
} catch {
    # Non-fatal
}

Write-Host "`nInstallation completed successfully!" -ForegroundColor Green
Write-Host "Commands available:" -ForegroundColor White
Write-Host "  agy-profile list              # List Google profiles & quotas" -ForegroundColor Yellow
Write-Host "  agy-profile switch <name|num> # Switch active profile" -ForegroundColor Yellow
Write-Host "  agy-profile auth <name|num>   # Authenticate with Google OAuth" -ForegroundColor Yellow
Write-Host "  agy-profile create <name>     # Create new profile`n" -ForegroundColor Yellow

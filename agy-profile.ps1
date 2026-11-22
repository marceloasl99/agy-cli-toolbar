# Antigravity Profile Manager PowerShell Wrapper
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)
$customScript = Join-Path $env:USERPROFILE ".antigravity-custom\profile_manager.py"
& python $customScript @ArgsList

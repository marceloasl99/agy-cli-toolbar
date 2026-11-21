# Antigravity Profile Manager PowerShell Wrapper
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)
& python "C:\Users\ma038\.antigravity-custom\profile_manager.py" @ArgsList

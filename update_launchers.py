import os

bin_dir = r"C:\Users\ma038\AppData\Local\agy\bin"
files = {
    "agy.cmd": ("perfil1", r"C:\Users\ma038"),
    "agy1.cmd": ("perfil1", r"C:\Users\ma038"),
    "agy2.cmd": ("perfil2", r"C:\Users\ma038\.agy-perfis\perfil2"),
    "agy3.cmd": ("perfil3", r"C:\Users\ma038\.agy-perfis\perfil3"),
    "agy4.cmd": ("perfil4", r"C:\Users\ma038\.agy-perfis\perfil4"),
}

for fname, (pname, proot) in files.items():
    fpath = os.path.join(bin_dir, fname)
    homepath = proot[2:]
    content = f"""@echo off
setlocal
set "AGY_PROFILE={pname}"
set "PERFIL_ROOT={proot}"
set "USERPROFILE=%PERFIL_ROOT%"
set "HOME=%PERFIL_ROOT%"
set "HOMEDRIVE=C:"
set "HOMEPATH={homepath}"
set "APPDATA=%PERFIL_ROOT%\\AppData\\Roaming"
set "LOCALAPPDATA=%PERFIL_ROOT%\\AppData\\Local"
set "GEMINI_HOME=%PERFIL_ROOT%"
set "ANTIGRAVITY_GEMINI_DIR=%PERFIL_ROOT%\\.gemini"
set "ANTIGRAVITY_APP_DATA_DIR=%PERFIL_ROOT%\\.gemini\\antigravity-cli"

if not exist "%APPDATA%\\Antigravity" mkdir "%APPDATA%\\Antigravity" >nul 2>&1
if not exist "%LOCALAPPDATA%" mkdir "%LOCALAPPDATA%" >nul 2>&1
if not exist "%ANTIGRAVITY_GEMINI_DIR%" mkdir "%ANTIGRAVITY_GEMINI_DIR%" >nul 2>&1
if not exist "%ANTIGRAVITY_APP_DATA_DIR%" mkdir "%ANTIGRAVITY_APP_DATA_DIR%" >nul 2>&1

python "C:\\Users\\ma038\\.antigravity-custom\\profile_manager.py" pre-run {pname} >nul 2>&1

"%~dp0agy.exe" %*

python "C:\\Users\\ma038\\.antigravity-custom\\profile_manager.py" post-run {pname} >nul 2>&1
endlocal
"""
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"Updated {fname} -> {pname}")

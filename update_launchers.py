import os

user_home = os.path.expanduser("~")
bin_dir = os.path.join(os.environ.get("LOCALAPPDATA", os.path.join(user_home, "AppData", "Local")), "agy", "bin")
profiles_base = os.path.join(user_home, ".agy-perfis")

files = {
    "agy.cmd": ("perfil1", os.path.join(profiles_base, "perfil1")),
    "agy1.cmd": ("perfil1", os.path.join(profiles_base, "perfil1")),
    "agy2.cmd": ("perfil2", os.path.join(profiles_base, "perfil2")),
    "agy3.cmd": ("perfil3", os.path.join(profiles_base, "perfil3")),
    "agy4.cmd": ("perfil4", os.path.join(profiles_base, "perfil4")),
    "agy5.cmd": ("agy5", os.path.join(profiles_base, "agy5")),
    "agy6.cmd": ("agy6", os.path.join(profiles_base, "agy6")),
}

custom_script = os.path.join(user_home, ".antigravity-custom", "profile_manager.py").replace("\\", "\\\\")

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

python "{custom_script}" pre-run {pname}

"%~dp0agy.exe" %*

python "{custom_script}" post-run {pname}
endlocal
"""
    try:
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {fname} -> {pname}")
    except Exception as e:
        print(f"Failed {fname}: {e}")

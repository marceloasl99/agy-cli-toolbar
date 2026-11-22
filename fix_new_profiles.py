"""Fix agy5/agy6 launchers, remove duplicate launchers, update quotas has_oauth."""
import os, json

user_home = os.path.expanduser("~")
bin_dir = os.path.join(os.environ.get("LOCALAPPDATA", ""), "agy", "bin")
profiles_base = os.path.join(user_home, ".agy-perfis")
custom_dir = os.path.join(user_home, ".antigravity-custom")
custom_script = os.path.join(custom_dir, "profile_manager.py").replace("\\", "\\\\")

def make_launcher(pname, proot):
    homepath = proot[2:]
    return f"""@echo off
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

python "{custom_script}" pre-run {pname} >nul 2>&1

"%~dp0agy.exe" %*

python "{custom_script}" post-run {pname} >nul 2>&1
endlocal
"""

# 1. Fix agy5.cmd and agy5.bat — add pre-run/post-run
for pname in ["agy5", "agy6"]:
    proot = os.path.join(profiles_base, pname)
    content = make_launcher(pname, proot)
    for ext in [".cmd", ".bat"]:
        fpath = os.path.join(bin_dir, pname + ext)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"[OK] Fixed {pname}{ext} with pre-run/post-run")

# 2. Remove duplicate/wrong launchers
for bad in ["agy-5.cmd", "agy-6.cmd", "agy-agy5.cmd", "agy-agy6.cmd"]:
    p = os.path.join(bin_dir, bad)
    if os.path.exists(p):
        os.remove(p)
        print(f"[REMOVED] {bad}")
    else:
        print(f"[SKIP] {bad} not found")

# 3. Fix profiles_quotas.json — has_oauth based on actual wincred.json
qfile = os.path.join(custom_dir, "profiles_quotas.json")
with open(qfile, "r", encoding="utf-8") as f:
    q = json.load(f)

for pkey in ["agy5", "agy6"]:
    wincred_path = os.path.join(profiles_base, pkey, ".gemini", "wincred.json")
    ga_path = os.path.join(profiles_base, pkey, ".gemini", "google_accounts.json")
    has_oauth = os.path.exists(wincred_path)
    email = ""
    if os.path.exists(ga_path):
        try:
            ga = json.load(open(ga_path, encoding="utf-8"))
            email = ga.get("active", "")
        except Exception:
            pass
    if pkey in q:
        q[pkey]["has_oauth"] = has_oauth
        q[pkey]["email"] = email
        print(f"[OK] {pkey}: has_oauth={has_oauth}, email={email!r}")

with open(qfile, "w", encoding="utf-8") as f:
    json.dump(q, f, indent=2, ensure_ascii=False)
print("[OK] profiles_quotas.json updated")

# 4. Report current bin directory contents
print("\nCurrent bin contents:")
for f in sorted(os.listdir(bin_dir)):
    print(f"  {f}")

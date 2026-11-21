import os
import sys
import json
import shutil
import subprocess
import datetime

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

USER_HOME = os.path.expanduser("~")
PROFILES_BASE_DIR = os.path.join(USER_HOME, ".agy-perfis")
CUSTOM_DIR = os.path.join(USER_HOME, ".antigravity-custom")
ACTIVE_PROFILE_FILE = os.path.join(CUSTOM_DIR, "active_profile.json")
QUOTAS_CACHE_FILE = os.path.join(CUSTOM_DIR, "profiles_quotas.json")
AGY_BIN_DIR = r"C:\Users\ma038\AppData\Local\agy\bin"
DESKTOP_EXE = r"C:\Users\ma038\AppData\Local\Programs\antigravity\Antigravity.exe"

# ANSI Colors
CYAN = "\033[96m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
MAGENTA = "\033[95m"
WHITE = "\033[97m"
GRAY = "\033[90m"
BOLD = "\033[1m"
RESET = "\033[0m"

def get_active_profile():
    if os.path.exists(ACTIVE_PROFILE_FILE):
        try:
            with open(ACTIVE_PROFILE_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d.get("active", "perfil1")
        except Exception:
            pass
    return "perfil1"

def set_active_profile(profile_name):
    os.makedirs(CUSTOM_DIR, exist_ok=True)
    with open(ACTIVE_PROFILE_FILE, "w", encoding="utf-8") as f:
        json.dump({"active": profile_name, "updated_at": datetime.datetime.now().isoformat()}, f, indent=2)

def discover_profiles():
    """Discovers all profiles on the system."""
    profiles = {
        "perfil1": {
            "name": "perfil1",
            "display": "Perfil 1 (Principal)",
            "root": USER_HOME,
            "gemini_dir": os.path.join(USER_HOME, ".gemini"),
            "is_default": True
        }
    }

    if os.path.exists(PROFILES_BASE_DIR):
        for item in sorted(os.listdir(PROFILES_BASE_DIR)):
            full_path = os.path.join(PROFILES_BASE_DIR, item)
            if os.path.isdir(full_path):
                # Accept folders starting with 'perfil' (e.g. perfil2, perfil3, perfil4)
                if not item.startswith("perfil"):
                    continue
                num_part = item[6:]
                disp = f"Perfil {num_part}" if num_part.isdigit() else item.capitalize()
                profiles[item] = {
                    "name": item,
                    "display": disp,
                    "root": full_path,
                    "gemini_dir": os.path.join(full_path, ".gemini"),
                    "is_default": False
                }
    return profiles

def get_profile_info(prof):
    gem_dir = prof["gemini_dir"]
    accounts_file = os.path.join(gem_dir, "google_accounts.json")
    oauth_file = os.path.join(gem_dir, "oauth_creds.json")

    email = "Desconhecido"
    has_oauth = os.path.exists(oauth_file)

    if os.path.exists(accounts_file):
        try:
            with open(accounts_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                email = d.get("active", email)
        except Exception:
            pass

    if email == "Desconhecido" and has_oauth:
        try:
            with open(oauth_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                id_tok = d.get("id_token", "")
                if "." in id_tok:
                    import base64
                    payload_b64 = id_tok.split(".")[1]
                    payload_b64 += "=" * ((4 - len(payload_b64) % 4) % 4)
                    claims = json.loads(base64.urlsafe_b64decode(payload_b64.encode()).decode())
                    email = claims.get("email", email)
        except Exception:
            pass

    # Read Quotas Cache
    quotas = {}
    if os.path.exists(QUOTAS_CACHE_FILE):
        try:
            with open(QUOTAS_CACHE_FILE, "r", encoding="utf-8") as f:
                all_q = json.load(f)
                quotas = all_q.get(prof["name"], {})
        except Exception:
            pass

    return {
        "email": email,
        "has_oauth": has_oauth,
        "quota_5h": quotas.get("quota_5h"),
        "quota_weekly": quotas.get("quota_weekly"),
        "quota_updated": quotas.get("updated_at")
    }

def make_mini_bar(pct, length=12):
    pct = min(max(pct, 0.0), 100.0)
    exact_blocks = length * (pct / 100.0)
    full_blocks = int(exact_blocks)
    remainder = exact_blocks - full_blocks
    partial_chars = ['', '▏', '▎', '▍', '▌', '▋', '▊', '▉']
    idx = int(round(remainder * 8))
    partial_char = ''
    if idx >= 8:
        full_blocks += 1
    elif idx > 0:
        partial_char = partial_chars[idx]
    empty_blocks = max(length - full_blocks - (1 if partial_char else 0), 0)
    bar = "█" * full_blocks + partial_char + "░" * empty_blocks
    col = GREEN if pct < 60 else (YELLOW if pct < 85 else RED)
    return f"{col}{bar}{RESET}"

def format_countdown(sec):
    if not sec or sec <= 0:
        return "pronto"
    h = int(sec // 3600)
    m = int((sec % 3600) // 60)
    return f"{h}h{m:02d}m" if h > 0 else f"{m}m"

def cmd_list():
    profiles = discover_profiles()
    active = get_active_profile()

    print(f"\n{BOLD}{CYAN}========================================================================================{RESET}")
    print(f"{BOLD}{WHITE}              PERFIS DO GOOGLE & QUOTAS - ANTIGRAVITY CLI ({len(profiles)} perfis){RESET}")
    print(f"{BOLD}{CYAN}========================================================================================{RESET}\n")

    for i, (key, prof) in enumerate(profiles.items(), 1):
        info = get_profile_info(prof)
        is_active = (key == active)
        active_tag = f"{BOLD}{GREEN}▶ ATIVO{RESET}" if is_active else f"{GRAY}       {RESET}"
        status_tag = f"{GREEN}✓ Conectado{RESET}" if info["has_oauth"] else f"{YELLOW}! Requer Auth{RESET}"
        
        print(f" {active_tag} {BOLD}[{i}] {prof['display']}{RESET}  {GRAY}(id: {key}){RESET}")
        print(f"     👤 Conta: {CYAN}{info['email']}{RESET}  │  Status: {status_tag}")
        
        # 5h Quota
        q5h = info["quota_5h"]
        if q5h:
            used5 = q5h.get("used_pct", 0.0)
            bar5 = make_mini_bar(used5, length=14)
            rst5 = format_countdown(q5h.get("reset_in_seconds", 0))
            col5 = GREEN if used5 < 60 else (YELLOW if used5 < 85 else RED)
            print(f"     ⏳ Cota 5h:  [{bar5}] {col5}{used5:4.1f}%{RESET} {GRAY}(reset em {rst5}){RESET}")
        else:
            bar_empty = make_mini_bar(0.0, length=14)
            print(f"     ⏳ Cota 5h:  [{bar_empty}] {GRAY}0.0% (sem histórico){RESET}")

        # Weekly Quota
        qw = info["quota_weekly"]
        if qw:
            used_w = qw.get("used_pct", 0.0)
            bar_w = make_mini_bar(used_w, length=14)
            rst_w = format_countdown(qw.get("reset_in_seconds", 0))
            col_w = GREEN if used_w < 60 else (YELLOW if used_w < 85 else RED)
            print(f"     📅 Cota 7d:  [{bar_w}] {col_w}{used_w:4.1f}%{RESET} {GRAY}(reset em {rst_w}){RESET}")
        else:
            bar_empty_w = make_mini_bar(0.0, length=14)
            print(f"     📅 Cota 7d:  [{bar_empty_w}] {GRAY}0.0% (sem histórico){RESET}")
        
        print(f"     📁 Pasta: {GRAY}{prof['root']}{RESET}\n")

    print(f"{GRAY}Para alternar:  agy-profile switch <número_ou_nome>{RESET}")
    print(f"{GRAY}Para login:     agy-profile auth <número_ou_nome>{RESET}")
    print(f"{GRAY}Para novo:      agy-profile create <nome> [email]{RESET}\n")

def cmd_switch(target):
    profiles = discover_profiles()
    current_active = get_active_profile()

    # Find profile by key or index
    chosen_key = None
    if target.isdigit():
        idx = int(target)
        keys = list(profiles.keys())
        if 1 <= idx <= len(keys):
            chosen_key = keys[idx - 1]
    else:
        target_lower = target.lower()
        for k in profiles.keys():
            if k.lower() == target_lower:
                chosen_key = k
                break

    if not chosen_key:
        print(f"{RED}[!] Perfil '{target}' não encontrado.{RESET}")
        print("Perfis disponíveis:")
        for i, k in enumerate(profiles.keys(), 1):
            print(f"  [{i}] {k}")
        return False

    if chosen_key == current_active:
        print(f"{YELLOW}[*] O perfil '{chosen_key}' já é o perfil ativo atualmente.{RESET}")
        return True

    target_prof = profiles[chosen_key]
    current_prof = profiles.get(current_active)

    # 1. Backup current active credentials back to its profile if not perfil1
    main_gemini = os.path.join(USER_HOME, ".gemini")
    if current_prof and not current_prof["is_default"]:
        cur_target_gemini = current_prof["gemini_dir"]
        os.makedirs(cur_target_gemini, exist_ok=True)
        for f in ["google_accounts.json", "oauth_creds.json"]:
            src = os.path.join(main_gemini, f)
            dst = os.path.join(cur_target_gemini, f)
            if os.path.exists(src):
                shutil.copy2(src, dst)

    # 2. Copy target profile credentials to main .gemini so global agy uses them
    if not target_prof["is_default"]:
        src_gemini = target_prof["gemini_dir"]
        for f in ["google_accounts.json", "oauth_creds.json"]:
            src = os.path.join(src_gemini, f)
            dst = os.path.join(main_gemini, f)
            if os.path.exists(src):
                shutil.copy2(src, dst)
            elif os.path.exists(dst):
                # If target doesn't have oauth yet, don't overwrite with old credentials
                pass

    set_active_profile(chosen_key)
    info = get_profile_info(target_prof)

    print(f"\n{BOLD}{GREEN}[✓] Perfil alternado com sucesso para: {chosen_key.upper()}!{RESET}")
    print(f"    👤 Conta ativa: {CYAN}{info['email']}{RESET}")
    print(f"    📁 Raiz: {GRAY}{target_prof['root']}{RESET}")
    print(f"    ⚡ As próximas sessões do Antigravity CLI e Desktop usarão este perfil.\n")
    return True

def cmd_create(name, email=None):
    if not name or not name.isalnum():
        name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).lower()

    profiles = discover_profiles()
    if name in profiles:
        print(f"{YELLOW}[!] Um perfil com o nome '{name}' já existe.{RESET}")
        return False

    prof_dir = os.path.join(PROFILES_BASE_DIR, name)
    gemini_dir = os.path.join(prof_dir, ".gemini")
    cli_dir = os.path.join(gemini_dir, "antigravity-cli")
    app_data = os.path.join(prof_dir, "AppData", "Roaming", "Antigravity")
    local_data = os.path.join(prof_dir, "AppData", "Local")

    os.makedirs(cli_dir, exist_ok=True)
    os.makedirs(app_data, exist_ok=True)
    os.makedirs(local_data, exist_ok=True)

    # Configure settings.json with custom statusline
    settings_file = os.path.join(cli_dir, "settings.json")
    statusline_script = os.path.join(CUSTOM_DIR, "statusline.py").replace("\\", "\\\\")
    default_settings = {
        "statusLine": {
            "type": "command",
            "command": f"python {statusline_script}",
            "padding": 0,
            "stack_with_default": False,
            "enabled": True
        }
    }
    with open(settings_file, "w", encoding="utf-8") as f:
        json.dump(default_settings, f, indent=2)

    # Configure google_accounts.json
    acc_file = os.path.join(gemini_dir, "google_accounts.json")
    acc_email = email if email else f"{name}@gmail.com"
    with open(acc_file, "w", encoding="utf-8") as f:
        json.dump({"active": acc_email, "old": []}, f, indent=2)

    # Create dedicated launcher script in AGY_BIN_DIR if it exists
    if os.path.exists(AGY_BIN_DIR):
        cmd_names = [f"agy-{name}.cmd"]
        if name.startswith("perfil") and name[6:].isdigit():
            cmd_names.append(f"agy{name[6:]}.cmd")
        elif name.isdigit():
            cmd_names.append(f"agy{name}.cmd")

        homepath = prof_dir[2:]
        cmd_content = f"""@echo off
setlocal
set "AGY_PROFILE={name}"
set "PERFIL_ROOT={prof_dir}"
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

"%~dp0agy.exe" %*
endlocal
"""
        for cname in cmd_names:
            try:
                with open(os.path.join(AGY_BIN_DIR, cname), "w", encoding="utf-8") as f:
                    f.write(cmd_content)
            except Exception:
                pass

    print(f"\n{BOLD}{GREEN}[✓] Perfil '{name}' criado com sucesso!{RESET}")
    print(f"    📁 Pasta: {prof_dir}")
    print(f"    👤 Email inicial: {acc_email}")
    print(f"\n{YELLOW}Próximo passo: Autentique a conta Google deste perfil:{RESET}")
    print(f"  {CYAN}agy-profile auth {name}{RESET}\n")
    return True

def cmd_auth(target):
    profiles = discover_profiles()
    chosen_key = None
    if target.isdigit():
        idx = int(target)
        keys = list(profiles.keys())
        if 1 <= idx <= len(keys):
            chosen_key = keys[idx - 1]
    else:
        for k in profiles.keys():
            if k.lower() == target.lower():
                chosen_key = k
                break

    if not chosen_key:
        print(f"{RED}[!] Perfil '{target}' não encontrado.{RESET}")
        return False

    prof = profiles[chosen_key]
    gem_dir = prof["gemini_dir"]

    print(f"\n{BOLD}{CYAN}======================================================{RESET}")
    print(f"{BOLD}{WHITE}     AUTENTICAÇÃO GOOGLE - PERFIL: {chosen_key.upper()}{RESET}")
    print(f"{BOLD}{CYAN}======================================================{RESET}")
    print("Escolha o método de autenticação:")
    print("  [1] Navegador Web (OAuth 2.0 automático via servidor local)")
    print("  [2] Abrir Antigravity Desktop no perfil (Login nativo 1-Clique)")
    print("  [3] Copiar credenciais do perfil principal (perfil1)")
    print("  [0] Cancelar\n")

    opt = input("Opção [1-3]: ").strip()
    if opt == "1":
        oauth_script = os.path.join(os.path.dirname(__file__), "oauth_auth.py")
        subprocess.run([sys.executable, oauth_script, gem_dir])
        info = get_profile_info(prof)
        print(f"\n{GREEN}[✓] Concluído! Conta autenticada: {info['email']}{RESET}\n")
    elif opt == "2":
        cmd_desktop(chosen_key)
        print(f"{GREEN}[*] Após fazer login no Desktop, as credenciais serão salvas no perfil automaticamente.{RESET}\n")
    elif opt == "3":
        src = os.path.join(USER_HOME, ".gemini", "oauth_creds.json")
        src_acc = os.path.join(USER_HOME, ".gemini", "google_accounts.json")
        if os.path.exists(src):
            os.makedirs(gem_dir, exist_ok=True)
            shutil.copy2(src, os.path.join(gem_dir, "oauth_creds.json"))
            if os.path.exists(src_acc):
                shutil.copy2(src_acc, os.path.join(gem_dir, "google_accounts.json"))
            info = get_profile_info(prof)
            print(f"\n{GREEN}[✓] Credenciais copiadas com sucesso! Conta: {info['email']}{RESET}\n")
        else:
            print(f"{RED}[!] Credenciais principais não encontradas.{RESET}\n")
    return True

def cmd_desktop(target):
    profiles = discover_profiles()
    chosen_key = None
    if target.isdigit():
        idx = int(target)
        keys = list(profiles.keys())
        if 1 <= idx <= len(keys):
            chosen_key = keys[idx - 1]
    else:
        for k in profiles.keys():
            if k.lower() == target.lower():
                chosen_key = k
                break

    if not chosen_key:
        print(f"{RED}[!] Perfil '{target}' não encontrado.{RESET}")
        return False

    prof = profiles[chosen_key]
    prof_root = prof["root"]
    app_data = os.path.join(prof_root, "AppData", "Roaming", "Antigravity")
    local_data = os.path.join(prof_root, "AppData", "Local")
    gemini_dir = prof["gemini_dir"]
    cli_dir = os.path.join(gemini_dir, "antigravity-cli")

    os.makedirs(app_data, exist_ok=True)
    os.makedirs(local_data, exist_ok=True)
    os.makedirs(gemini_dir, exist_ok=True)
    os.makedirs(cli_dir, exist_ok=True)

    env = os.environ.copy()
    env["USERPROFILE"] = prof_root
    env["HOME"] = prof_root
    env["APPDATA"] = os.path.join(prof_root, "AppData", "Roaming")
    env["LOCALAPPDATA"] = local_data
    env["GEMINI_HOME"] = prof_root
    env["ANTIGRAVITY_GEMINI_DIR"] = gemini_dir
    env["ANTIGRAVITY_APP_DATA_DIR"] = cli_dir
    env["AGY_PROFILE"] = chosen_key

    print(f"{CYAN}[*] Iniciando Antigravity Desktop no perfil {chosen_key}...{RESET}")
    subprocess.Popen([DESKTOP_EXE, f"--user-data-dir={app_data}"], env=env)
    return True

def cmd_run(target, extra_args):
    profiles = discover_profiles()
    chosen_key = None
    if target.isdigit():
        idx = int(target)
        keys = list(profiles.keys())
        if 1 <= idx <= len(keys):
            chosen_key = keys[idx - 1]
    else:
        for k in profiles.keys():
            if k.lower() == target.lower():
                chosen_key = k
                break

    if not chosen_key:
        print(f"{RED}[!] Perfil '{target}' não encontrado.{RESET}")
        return False

    prof = profiles[chosen_key]
    prof_root = prof["root"]
    gemini_dir = prof["gemini_dir"]
    cli_dir = os.path.join(gemini_dir, "antigravity-cli")

    env = os.environ.copy()
    env["USERPROFILE"] = prof_root
    env["HOME"] = prof_root
    env["APPDATA"] = os.path.join(prof_root, "AppData", "Roaming")
    env["LOCALAPPDATA"] = os.path.join(prof_root, "AppData", "Local")
    env["GEMINI_HOME"] = prof_root
    env["ANTIGRAVITY_GEMINI_DIR"] = gemini_dir
    env["ANTIGRAVITY_APP_DATA_DIR"] = cli_dir
    env["AGY_PROFILE"] = chosen_key

    agy_exe = os.path.join(AGY_BIN_DIR, "agy.exe")
    cmd = [agy_exe] + extra_args
    subprocess.run(cmd, env=env)
    return True

def cmd_tray():
    tray_script = os.path.join(CUSTOM_DIR, "tray_app.pyw")
    if not os.path.exists(tray_script):
        tray_script = os.path.join(os.path.dirname(__file__), "tray_app.pyw")
    print(f"{CYAN}[*] Iniciando Antigravity Tray & Desktop Widget em segundo plano...{RESET}")
    subprocess.Popen(["pythonw", tray_script])
    print(f"{GREEN}[✓] App iniciado na bandeja do sistema (perto do relógio)!{RESET}")
    return True

def cmd_autostart(enable=True):
    startup_dir = os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")
    shortcut_vbs = os.path.join(startup_dir, "AntigravityTray.vbs")
    tray_script = os.path.join(CUSTOM_DIR, "tray_app.pyw")
    if enable:
        vbs_content = f'CreateObject("Wscript.Shell").Run "pythonw \"{tray_script}\"", 0, False\n'
        try:
            with open(shortcut_vbs, "w", encoding="utf-8") as f:
                f.write(vbs_content)
            print(f"{GREEN}[✓] Inicialização automática com o Windows ativada com sucesso!{RESET}")
        except Exception as e:
            print(f"{RED}[!] Erro ao ativar inicialização: {e}{RESET}")
    else:
        if os.path.exists(shortcut_vbs):
            os.remove(shortcut_vbs)
            print(f"{YELLOW}[✓] Inicialização automática desativada.{RESET}")
        else:
            print(f"{GRAY}[*] A inicialização automática já estava desativada.{RESET}")
    return True

def interactive_menu():
    while True:
        profiles = discover_profiles()
        active = get_active_profile()
        print(f"\n{BOLD}{CYAN}=================================================================={RESET}")
        print(f"{BOLD}{WHITE}             GERENCIADOR DE PERFIS ANTIGRAVITY (AGY){RESET}")
        print(f"{BOLD}{CYAN}=================================================================={RESET}")
        print(f" Perfil Ativo Atual: {BOLD}{GREEN}{active.upper()}{RESET}")
        print(f" Perfis Disponíveis: {WHITE}{', '.join(profiles.keys())}{RESET}\n")
        print(" [1] 📊 Listar todos os perfis e quotas das contas")
        print(" [2] 🔄 Alternar perfil ativo (Switch)")
        print(" [3] ➕ Criar novo perfil")
        print(" [4] 🔑 Autenticar perfil com Google OAuth")
        print(" [5] 🖥️  Abrir Antigravity Desktop no perfil")
        print(" [6] ⚡ Executar agy CLI no perfil")
        print(" [7] 📊 Iniciar Tray & Widget no Desktop")
        print(" [8] 🚀 Ativar/Desativar Inicialização com o Windows")
        print(" [0] ❌ Sair\n")

        choice = input("Escolha uma opção [0-8]: ").strip()
        if choice == "1":
            cmd_list()
        elif choice == "2":
            cmd_list()
            target = input("Número ou nome do perfil para ativar: ").strip()
            if target:
                cmd_switch(target)
        elif choice == "3":
            nome = input("Nome do novo perfil (ex: trabalho, pessoal): ").strip()
            email = input("Email do Google (opcional): ").strip()
            if nome:
                cmd_create(nome, email if email else None)
        elif choice == "4":
            cmd_list()
            target = input("Número ou nome do perfil para autenticar: ").strip()
            if target:
                cmd_auth(target)
        elif choice == "5":
            cmd_list()
            target = input("Número ou nome do perfil para abrir no Desktop: ").strip()
            if target:
                cmd_desktop(target)
        elif choice == "6":
            cmd_list()
            target = input("Número ou nome do perfil para rodar o CLI: ").strip()
            if target:
                cmd_run(target, [])
        elif choice == "7":
            cmd_tray()
        elif choice == "8":
            sub_c = input("Ativar inicialização automática com o Windows? [s/n]: ").strip().lower()
            cmd_autostart(sub_c in ("s", "sim", "y", "yes", "1"))
        elif choice == "0":
            break
        else:
            print(f"{RED}Opção inválida.{RESET}")

def main():
    if len(sys.argv) == 1:
        interactive_menu()
        return

    subcmd = sys.argv[1].lower()
    if subcmd in ("list", "quota", "quotas", "status", "ls"):
        cmd_list()
    elif subcmd in ("switch", "use", "set", "select"):
        if len(sys.argv) > 2:
            cmd_switch(sys.argv[2])
        else:
            cmd_list()
            target = input("Número ou nome do perfil: ").strip()
            if target:
                cmd_switch(target)
    elif subcmd in ("create", "add", "new"):
        if len(sys.argv) > 2:
            nome = sys.argv[2]
            email = sys.argv[3] if len(sys.argv) > 3 else None
            cmd_create(nome, email)
        else:
            nome = input("Nome do novo perfil: ").strip()
            email = input("Email (opcional): ").strip()
            if nome:
                cmd_create(nome, email if email else None)
    elif subcmd in ("auth", "login"):
        if len(sys.argv) > 2:
            cmd_auth(sys.argv[2])
        else:
            cmd_list()
            target = input("Número ou nome do perfil para login: ").strip()
            if target:
                cmd_auth(target)
    elif subcmd in ("desktop", "gui"):
        target = sys.argv[2] if len(sys.argv) > 2 else get_active_profile()
        cmd_desktop(target)
    elif subcmd in ("run", "exec"):
        if len(sys.argv) > 2:
            cmd_run(sys.argv[2], sys.argv[3:])
        else:
            print("Uso: agy-profile run <perfil> [argumentos do agy...]")
    elif subcmd in ("tray", "widget", "gui"):
        cmd_tray()
    elif subcmd in ("autostart", "startup"):
        enable = True
        if len(sys.argv) > 2:
            enable = sys.argv[2].lower() in ("on", "1", "true", "enable", "sim", "s")
        cmd_autostart(enable)
    else:
        print(f"Comando desconhecido: {subcmd}")
        print("Comandos disponíveis: list, switch, create, auth, desktop, run, tray, autostart")

if __name__ == "__main__":
    main()

import os
import sys
import json
import shutil
import subprocess
import datetime
import ctypes

# Ensure UTF-8 output on Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

def _detect_user_home():
    """Resolves the real user home even when a .cmd launcher temporarily overrides USERPROFILE/HOME."""
    orig = os.environ.get("AGY_ORIG_HOME")
    if orig and os.path.isdir(orig):
        return orig
    pr = os.environ.get("PERFIL_ROOT")
    if pr:
        parent = os.path.dirname(os.path.normpath(pr))
        if os.path.basename(parent) == ".agy-perfis":
            return os.path.dirname(parent)
    return os.path.expanduser("~")

USER_HOME = _detect_user_home()
PROFILES_BASE_DIR = os.path.join(USER_HOME, ".agy-perfis")
CUSTOM_DIR = os.path.join(USER_HOME, ".antigravity-custom")
ACTIVE_PROFILE_FILE = os.path.join(CUSTOM_DIR, "active_profile.json")
QUOTAS_CACHE_FILE = os.path.join(CUSTOM_DIR, "profiles_quotas.json")
WORKDIRS_FILE = os.path.join(CUSTOM_DIR, "profile_workdirs.json")
LAUNCH_FILE = os.path.join(CUSTOM_DIR, "profile_launch.json")
IDENTITY_FILE = "profile_identity.json"
SESSION_MARKER = ".agy_session.json"
_BASE_LOCALAPPDATA = os.path.join(USER_HOME, "AppData", "Local") if os.environ.get("PERFIL_ROOT") else os.environ.get("LOCALAPPDATA", os.path.join(USER_HOME, "AppData", "Local"))
AGY_BIN_DIR = os.path.join(_BASE_LOCALAPPDATA, "agy", "bin")
CUSTOM_BIN_DIR = os.path.join(CUSTOM_DIR, "bin")
DESKTOP_EXE = os.path.join(_BASE_LOCALAPPDATA, "Programs", "antigravity", "Antigravity.exe")

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

# Windows Credential Manager Interop (Advapi32.dll)
import ctypes
from ctypes import wintypes

try:
    Advapi32 = ctypes.WinDLL("Advapi32.dll")

    class CREDENTIAL(ctypes.Structure):
        _fields_ = [
            ('Flags', wintypes.DWORD),
            ('Type', wintypes.DWORD),
            ('TargetName', wintypes.LPWSTR),
            ('Comment', wintypes.LPWSTR),
            ('LastWritten', wintypes.FILETIME),
            ('CredentialBlobSize', wintypes.DWORD),
            ('CredentialBlob', ctypes.POINTER(ctypes.c_byte)),
            ('Persist', wintypes.DWORD),
            ('AttributeCount', wintypes.DWORD),
            ('Attributes', ctypes.c_void_p),
            ('TargetAlias', wintypes.LPWSTR),
            ('UserName', wintypes.LPWSTR),
        ]
except Exception:
    Advapi32 = None

def read_wincred(target="gemini:antigravity"):
    if not Advapi32:
        return None
    try:
        CredReadW = Advapi32.CredReadW
        CredReadW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD, ctypes.POINTER(ctypes.POINTER(CREDENTIAL))]
        CredReadW.restype = wintypes.BOOL
        pcred = ctypes.POINTER(CREDENTIAL)()
        if CredReadW(target, 1, 0, ctypes.byref(pcred)):
            cred = pcred.contents
            blob = ctypes.string_at(cred.CredentialBlob, cred.CredentialBlobSize).decode("utf-8", errors="ignore")
            Advapi32.CredFree(pcred)
            try:
                return json.loads(blob)
            except Exception:
                return blob
    except Exception:
        pass
    return None

def write_wincred(data, target="gemini:antigravity"):
    if not Advapi32:
        return False
    try:
        CredWriteW = Advapi32.CredWriteW
        CredWriteW.argtypes = [ctypes.POINTER(CREDENTIAL), wintypes.DWORD]
        CredWriteW.restype = wintypes.BOOL
        if isinstance(data, (dict, list)):
            blob = json.dumps(data).encode("utf-8")
        else:
            blob = str(data).encode("utf-8")
        c = CREDENTIAL()
        c.Flags = 0
        c.Type = 1  # CRED_TYPE_GENERIC
        c.TargetName = target
        c.Comment = None
        c.CredentialBlobSize = len(blob)
        c.CredentialBlob = ctypes.cast(ctypes.create_string_buffer(blob), ctypes.POINTER(ctypes.c_byte))
        c.Persist = 2  # CRED_PERSIST_LOCAL_MACHINE
        c.AttributeCount = 0
        c.Attributes = None
        c.TargetAlias = None
        c.UserName = "antigravity"
        return bool(CredWriteW(ctypes.byref(c), 0))
    except Exception:
        return False

def delete_wincred(target="gemini:antigravity"):
    if not Advapi32:
        return False
    try:
        CredDeleteW = Advapi32.CredDeleteW
        CredDeleteW.argtypes = [wintypes.LPCWSTR, wintypes.DWORD, wintypes.DWORD]
        CredDeleteW.restype = wintypes.BOOL
        return bool(CredDeleteW(target, 1, 0))
    except Exception:
        return False

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
    profiles = {}
    p1_dir = os.path.join(PROFILES_BASE_DIR, "perfil1")
    if os.path.exists(p1_dir):
        profiles["perfil1"] = {
            "name": "perfil1",
            "display": "Perfil 1 (Principal)",
            "root": p1_dir,
            "gemini_dir": os.path.join(p1_dir, ".gemini"),
            "is_default": True
        }
    else:
        profiles["perfil1"] = {
            "name": "perfil1",
            "display": "Perfil 1 (Principal)",
            "root": USER_HOME,
            "gemini_dir": os.path.join(USER_HOME, ".gemini"),
            "is_default": True
        }

    if os.path.exists(PROFILES_BASE_DIR):
        numbered_profiles = []
        custom_profiles = []
        for item in os.listdir(PROFILES_BASE_DIR):
            if item == "perfil1" or item.startswith(".") or item.startswith("__"):
                continue
            full_path = os.path.join(PROFILES_BASE_DIR, item)
            if os.path.isdir(full_path):
                if item.startswith("perfil") and item[6:].isdigit():
                    num = int(item[6:])
                    numbered_profiles.append((num, item, full_path, f"Perfil {num}"))
                elif item.startswith("agy") and item[3:].isdigit():
                    num = int(item[3:])
                    numbered_profiles.append((num, item, full_path, f"Perfil {num} ({item})"))
                elif item.isdigit():
                    num = int(item)
                    numbered_profiles.append((num, item, full_path, f"Perfil {num}"))
                else:
                    custom_profiles.append((item, full_path))

        # Adiciona primeiro os numerados padrão em ordem crescente (perfil2, perfil3, perfil4, agy5, agy6...)
        for num, item, full_path, disp in sorted(numbered_profiles, key=lambda x: x[0]):
            profiles[item] = {
                "name": item,
                "display": disp,
                "root": full_path,
                "gemini_dir": os.path.join(full_path, ".gemini"),
                "is_default": False
            }

        # Depois adiciona os perfis adicionais/customizados em ordem alfabética
        for item, full_path in sorted(custom_profiles, key=lambda x: x[0].lower()):
            profiles[item] = {
                "name": item,
                "display": item,
                "root": full_path,
                "gemini_dir": os.path.join(full_path, ".gemini"),
                "is_default": False
            }
    return profiles

# Antigravity Model Groups & Quota Families (exact models from `agy models`)
GEMINI_MODELS = [
    "Gemini 3.8 Flash (Low)",
    "Gemini 3.8 Flash (Medium)",
    "Gemini 3.8 Flash (High)",
]
OUTROS_MODELS = [
    "Claude Sonnet 4.6 (Thinking)",
    "Claude Opus 4.6 (Thinking)",
    "GPT-OSS 120B (Medium)",
]
ARGON_MODELS = [
    "Gemini 4 Argon (Low / Medium / High)",
    "Gemini 4 Hydrogen (Low / Medium / High / XHigh)",
    "Gemini 4 Neon (Low / Medium / High / XHigh)",
    "Orchestrator (Neon / Argon)",
]

def get_profile_identity(name, profiles=None):
    """Returns bound email for profile from profile_identity.json, or None."""
    if profiles is None:
        profiles = discover_profiles()
    prof = profiles.get(name)
    if not prof:
        return None
    id_path = os.path.join(prof["gemini_dir"], IDENTITY_FILE)
    if os.path.exists(id_path):
        try:
            with open(id_path, "r", encoding="utf-8") as f:
                email = json.load(f).get("email")
                return email.strip() if isinstance(email, str) and email.strip() else None
        except Exception:
            pass
    return None

def set_profile_identity(name, email, profiles=None):
    """Binds profile to a canonical email in profile_identity.json."""
    if profiles is None:
        profiles = discover_profiles()
    prof = profiles.get(name)
    if not prof:
        return False
    os.makedirs(prof["gemini_dir"], exist_ok=True)
    id_path = os.path.join(prof["gemini_dir"], IDENTITY_FILE)
    with open(id_path, "w", encoding="utf-8") as f:
        json.dump({"email": email, "bound_at": datetime.datetime.now().isoformat()}, f, indent=2)
    return True

def _valid_cred(c):
    """Returns True if credential dict contains a token and id_token_email."""
    return isinstance(c, dict) and bool(c.get("token")) and bool(c.get("id_token_email"))

def _quarantine(path):
    """Renames a file to .quarantine-YYYYmmdd-HHMMSS instead of deleting it."""
    if os.path.exists(path):
        ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        dst = f"{path}.quarantine-{ts}"
        try:
            os.replace(path, dst)
            return dst
        except Exception:
            try:
                shutil.move(path, dst)
                return dst
            except Exception:
                pass
    return None

def _session_marker_path(gemini_dir):
    return os.path.join(gemini_dir, SESSION_MARKER)

def _read_session_marker(gemini_dir):
    p = _session_marker_path(gemini_dir)
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def _write_session_marker(gemini_dir, loaded_email):
    os.makedirs(gemini_dir, exist_ok=True)
    with open(_session_marker_path(gemini_dir), "w", encoding="utf-8") as f:
        json.dump({
            "loaded_email": loaded_email,
            "started_at": datetime.datetime.now().isoformat()
        }, f, indent=2)

def _remove_session_marker(gemini_dir):
    p = _session_marker_path(gemini_dir)
    if os.path.exists(p):
        try:
            os.remove(p)
        except Exception:
            pass

def get_profile_info(prof):
    gem_dir = prof["gemini_dir"]
    wincred_file = os.path.join(gem_dir, "wincred.json")
    accounts_file = os.path.join(gem_dir, "google_accounts.json")
    oauth_file = os.path.join(gem_dir, "oauth_creds.json")
    id_file = os.path.join(gem_dir, IDENTITY_FILE)

    email = "Desconhecido"
    has_oauth = False

    # 1. Prefer profile's own wincred.json
    if os.path.exists(wincred_file):
        try:
            with open(wincred_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                email = d.get("id_token_email", email)
                has_oauth = bool(d.get("token"))
        except Exception:
            pass

    # 2. Check profile's identity file
    if email == "Desconhecido" and os.path.exists(id_file):
        try:
            with open(id_file, "r", encoding="utf-8") as f:
                email = json.load(f).get("email", email) or email
        except Exception:
            pass

    # 3. Check profile's google_accounts.json
    if email == "Desconhecido" and os.path.exists(accounts_file):
        try:
            with open(accounts_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                email = d.get("active", email)
        except Exception:
            pass

    # 4. Check profile's oauth_creds.json
    if os.path.exists(oauth_file):
        has_oauth = True
        if email == "Desconhecido":
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

    gemini_5h = quotas.get("gemini_5h") or quotas.get("quota_5h")
    gemini_7d = quotas.get("gemini_7d") or quotas.get("quota_weekly")
    outros_3p = quotas.get("outros_3p")
    argon = quotas.get("argon")

    pro_profiles = {}
    widget_cfg_file = os.path.join(CUSTOM_DIR, "widget_config.json")
    if os.path.exists(widget_cfg_file):
        try:
            with open(widget_cfg_file, "r", encoding="utf-8") as f:
                pro_profiles = json.load(f).get("pro_profiles", {})
        except Exception:
            pass

    if prof["name"] in pro_profiles:
        is_pro = bool(pro_profiles[prof["name"]])
    else:
        is_pro = bool(quotas.get("is_pro") or prof["name"] == "perfil4" or argon)

    return {
        "email": email,
        "has_oauth": has_oauth,
        "is_pro": is_pro,
        "gemini_5h": gemini_5h,
        "gemini_7d": gemini_7d,
        "outros_3p": outros_3p,
        "argon": argon if is_pro else None,
        "gemini_models": GEMINI_MODELS,
        "outros_models": OUTROS_MODELS,
        "argon_models": ARGON_MODELS if is_pro else [],
        "quota_5h": gemini_5h,
        "quota_weekly": gemini_7d,
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
        tier_badge = f"{BOLD}{MAGENTA}[PRO PLAN]{RESET}" if info["is_pro"] else f"{GRAY}[PADRÃO]{RESET}"
        print(f"     👤 Conta: {CYAN}{info['email']}{RESET}  │  Status: {status_tag}  │  {tier_badge}")
        
        # 1. COTA GEMINI (5h e 7d)
        q5h = info["gemini_5h"]
        if q5h:
            used5 = q5h.get("used_pct", 0.0)
            bar5 = make_mini_bar(used5, length=14)
            rst5 = format_countdown(q5h.get("reset_in_seconds", 0))
            col5 = GREEN if used5 < 60 else (YELLOW if used5 < 85 else RED)
            print(f"     ★ Gemini (5h)  : [{bar5}] {col5}{used5:4.1f}%{RESET} {GRAY}(reset em {rst5}){RESET}")
        else:
            bar_empty = make_mini_bar(0.0, length=14)
            print(f"     ★ Gemini (5h)  : [{bar_empty}] {GRAY}0.0% (sem histórico){RESET}")

        qw = info["gemini_7d"]
        if qw:
            used_w = qw.get("used_pct", 0.0)
            bar_w = make_mini_bar(used_w, length=14)
            rst_w = format_countdown(qw.get("reset_in_seconds", 0))
            col_w = GREEN if used_w < 60 else (YELLOW if used_w < 85 else RED)
            print(f"     📅 Gemini (7d)  : [{bar_w}] {col_w}{used_w:4.1f}%{RESET} {GRAY}(reset em {rst_w}){RESET}")
        else:
            bar_empty_w = make_mini_bar(0.0, length=14)
            print(f"     📅 Gemini (7d)  : [{bar_empty_w}] {GRAY}0.0% (sem histórico){RESET}")
        print(f"        {GRAY}↳ Modelos Gemini    :{RESET} {CYAN}Gemini 3.8 Flash (Low, Medium, High){RESET}")

        # 2. COTA OUTROS (GPT / CLAUDE)
        qo = info.get("outros_3p")
        if qo:
            used_o = qo.get("used_pct", 0.0)
            bar_o = make_mini_bar(used_o, length=14)
            rst_o = format_countdown(qo.get("reset_in_seconds", 0))
            col_o = GREEN if used_o < 60 else (YELLOW if used_o < 85 else RED)
            print(f"     ⚡ Outros (3P)  : [{bar_o}] {col_o}{used_o:4.1f}%{RESET} {GRAY}(reset em {rst_o}){RESET}")
        else:
            bar_empty_o = make_mini_bar(0.0, length=14)
            print(f"     ⚡ Outros (3P)  : [{bar_empty_o}] {GREEN} 0.0%{RESET} {GRAY}(disponível){RESET}")
        print(f"        {GRAY}↳ Modelos GPT/Claude:{RESET} {YELLOW}Claude Sonnet 4.6 (Thinking), Claude Opus 4.6 (Thinking), GPT-OSS 120B (Medium){RESET}")

        # 3. COTA ARGON (SE CONTA PRO)
        if info["is_pro"]:
            qa = info.get("argon")
            if qa:
                used_a = qa.get("used_pct", 0.0)
                bar_a = make_mini_bar(used_a, length=14)
                rst_a = format_countdown(qa.get("reset_in_seconds", 0))
                col_a = GREEN if used_a < 60 else (YELLOW if used_a < 85 else RED)
                print(f"     ✦ Argon (Pro)  : [{bar_a}] {col_a}{used_a:4.1f}%{RESET} {GRAY}(reset em {rst_a}){RESET}")
            else:
                bar_empty_a = make_mini_bar(0.0, length=14)
                print(f"     ✦ Argon (Pro)  : [{bar_empty_a}] {GREEN} 0.0%{RESET} {GRAY}(disponível){RESET}")
            print(f"        {GRAY}↳ Modelos Argon     :{RESET} {MAGENTA}Gemini 4 Argon / Hydrogen / Neon, Orchestrator{RESET}")
        
        print(f"     📁 Pasta: {GRAY}{prof['root']}{RESET}\n")

    print(f"{GRAY}Para alternar:  agy-profile switch <número_ou_nome>{RESET}")
    print(f"{GRAY}Para login:     agy-profile auth <número_ou_nome>{RESET}")
    print(f"{GRAY}Para novo:      agy-profile create <nome> [email]{RESET}\n")

def pre_run(target_profile, launch_file=None, user_args=None):
    """
    Called before agy runs for target_profile.
    Swaps Windows Credential Manager token strictly from target_profile's own
    identity-verified wincred.json, and prepares launch folder + permission args.
    """
    profiles = discover_profiles()
    dry_run = bool(os.environ.get("AGY_LAUNCH_DRY_RUN"))

    # If profile does not exist yet, auto-create its isolated structure on the fly!
    if target_profile not in profiles:
        prof_root = os.path.join(PROFILES_BASE_DIR, target_profile)
        p_gem = os.path.join(prof_root, ".gemini")
        os.makedirs(p_gem, exist_ok=True)
        os.makedirs(os.path.join(prof_root, "AppData", "Roaming", "Antigravity"), exist_ok=True)
        os.makedirs(os.path.join(prof_root, "AppData", "Local"), exist_ok=True)
        p_cli = os.path.join(p_gem, "antigravity-cli")
        c_cli = os.path.join(USER_HOME, ".gemini", "antigravity-cli")
        if not is_ntfs_junction(p_cli) and not os.path.exists(p_cli):
            create_directory_junction(p_cli, c_cli)
        print(f"\n{BOLD}{CYAN}[✓] Novo perfil isolado '{target_profile}' criado com sucesso em:{RESET} {prof_root}")
        print(f"{YELLOW}[!] Este perfil ainda não possui conta Google conectada.{RESET}")
        print(f"{BOLD}[i] Por favor, faça login com sua conta quando solicitado a seguir...{RESET}\n")
        sync_profile_to_config_and_launchers(target_profile)
        profiles = discover_profiles()

    target_gemini = profiles[target_profile]["gemini_dir"]
    wincred_file = os.path.join(target_gemini, "wincred.json")
    identity = get_profile_identity(target_profile, profiles)

    loaded = False
    loaded_email = None
    if os.path.exists(wincred_file):
        try:
            with open(wincred_file, "r", encoding="utf-8") as f:
                t_cred = json.load(f)
            if _valid_cred(t_cred):
                cred_email = t_cred.get("id_token_email")
                if identity is None or cred_email == identity:
                    if not dry_run:
                        write_wincred(t_cred)
                    loaded = True
                    loaded_email = cred_email
                else:
                    qpath = _quarantine(wincred_file)
                    print(f"\n{YELLOW}[!] Credencial contaminada em '{target_profile}' ({cred_email} != identidade '{identity}').{RESET}")
                    if qpath:
                        print(f"{GRAY}    Arquivo movido para quarentena: {os.path.basename(qpath)}{RESET}")
        except Exception:
            pass

    if not loaded:
        if not dry_run:
            delete_wincred()
        print(f"\n{BOLD}{YELLOW}======================================================================{RESET}")
        print(f"{BOLD}{YELLOW}⚠️  PERFIL '{target_profile.upper()}' SEM CONTA CONECTADA{RESET}")
        if identity:
            print(f"    Conta esperada: {CYAN}{identity}{RESET}")
        else:
            print(f"    Nenhuma sessão salva encontrada para este perfil.")
        print(f"{CYAN}    Faça login com a conta Google deste perfil para autenticar.{RESET}")
        print(f"{BOLD}{YELLOW}======================================================================{RESET}\n")

    if not dry_run:
        _write_session_marker(target_gemini, loaded_email)
        set_active_profile(target_profile)

    # Launch options step (default folder + permission mode)
    if launch_file is not None:
        uargs = list(user_args) if user_args else []
        display_email = loaded_email or identity or "sem conta"
        workdir = get_workdir_for_profile(target_profile)
        opts = get_profile_launch_opts(target_profile)
        permission = opts.get("permission", "default")
        ask = bool(opts.get("ask_on_launch", True))

        should_pick = (
            ask
            and len(uargs) == 0
            and sys.stdin.isatty()
            and not os.environ.get("AGY_NO_PICKER")
        )
        if should_pick:
            picked = launch_picker(target_profile, display_email, workdir, permission)
            if picked is None:
                return "cancel"
            workdir, permission = picked
        else:
            wd_disp = workdir if (workdir and os.path.isdir(workdir)) else "(pasta atual)"
            perm_label = PERMISSION_PRESETS.get(permission, PERMISSION_PRESETS["default"])[0]
            print(f"{GRAY}[agy] 📂 {wd_disp} · 🔐 {perm_label}{RESET}")

        if workdir and os.path.isdir(workdir):
            ensure_trusted_workspace(target_profile, workdir)
        extra_launch_args = build_agy_args(permission, uargs)
        write_launch_file(launch_file, workdir if (workdir and os.path.isdir(workdir)) else None, extra_launch_args)

    return True

def post_run(target_profile):
    """
    Called after agy exits for target_profile.
    Captures updated tokens ONLY when they match target_profile's bound identity
    (or during a safe first login), preventing cross-profile contamination.
    """
    profiles = discover_profiles()
    if target_profile not in profiles:
        return False

    target_gemini = profiles[target_profile]["gemini_dir"]
    try:
        cred = read_wincred()
        if not _valid_cred(cred):
            return True

        email = cred.get("id_token_email")
        identity = get_profile_identity(target_profile, profiles)
        marker = _read_session_marker(target_gemini)

        # Find if another profile already owns this email
        other_owner = None
        for pname in profiles:
            if pname == target_profile:
                continue
            pid = get_profile_identity(pname, profiles)
            if pid and pid.lower() == email.lower():
                other_owner = pname
                break

        accepted = False
        if identity is not None:
            if email.lower() == identity.lower():
                accepted = True
        else:
            if marker is not None:
                m_email = marker.get("loaded_email")
                if m_email is None or m_email.lower() == email.lower():
                    if other_owner is None:
                        accepted = True
            elif other_owner is None:
                accepted = True

            if not accepted and other_owner is not None and sys.stdin.isatty():
                ans = input(f"{YELLOW}[!] A conta {email} já pertence ao perfil '{other_owner}'. Salvar também em '{target_profile}'? [s/N]: {RESET}").strip().lower()
                if ans in ("s", "sim", "y", "yes"):
                    accepted = True

        if accepted:
            os.makedirs(target_gemini, exist_ok=True)
            with open(os.path.join(target_gemini, "wincred.json"), "w", encoding="utf-8") as f:
                json.dump(cred, f, indent=2)
            with open(os.path.join(target_gemini, "google_accounts.json"), "w", encoding="utf-8") as f:
                json.dump({"active": email, "old": []}, f, indent=2)
            if identity is None:
                set_profile_identity(target_profile, email, profiles)
        else:
            exp = identity or "nenhuma (outra conta detectada)"
            print(f"{YELLOW}[!] Credencial atual ({email}) não pertence ao perfil '{target_profile}' (esperado: {exp}). Nada foi alterado.{RESET}")
        return True
    finally:
        _remove_session_marker(target_gemini)

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

    # Apply Windows Credential Manager switch
    pre_run(chosen_key)

    target_prof = profiles[chosen_key]
    info = get_profile_info(target_prof)

    print(f"\n{BOLD}{GREEN}[✓] Perfil alternado com sucesso para: {chosen_key.upper()}!{RESET}")
    print(f"    👤 Conta ativa: {CYAN}{info['email']}{RESET}")
    print(f"    📁 Raiz: {GRAY}{target_prof['root']}{RESET}")
    print(f"    ⚡ As próximas sessões do Antigravity CLI e Desktop usarão este perfil.\n")
    return True

def get_launcher_filename(name):
    """Returns canonical .cmd launcher filename for a profile."""
    if name.startswith("perfil") and name[6:].isdigit():
        return f"agy{name[6:]}.cmd"
    if name.startswith("agy") and name[3:].isdigit():
        return f"{name}.cmd"
    if name.isdigit():
        return f"agy{name}.cmd"
    return f"{name}.cmd"

def generate_launcher_content(name, prof_dir):
    """Generates canonical .cmd launcher script content for a profile."""
    script_path = os.path.join(CUSTOM_DIR, "profile_manager.py")
    homepath = prof_dir[2:] if len(prof_dir) > 2 and prof_dir[1] == ":" else prof_dir
    homedrive = prof_dir[:2] if len(prof_dir) > 1 and prof_dir[1] == ":" else "C:"
    return f"""@echo off
setlocal
set "AGY_PROFILE={name}"
set "AGY_ORIG_HOME={USER_HOME}"
set "PERFIL_ROOT={prof_dir}"
set "USERPROFILE=%PERFIL_ROOT%"
set "HOME=%PERFIL_ROOT%"
set "HOMEDRIVE={homedrive}"
set "HOMEPATH={homepath}"
set "APPDATA=%PERFIL_ROOT%\\AppData\\Roaming"
set "LOCALAPPDATA=%PERFIL_ROOT%\\AppData\\Local"
set "GEMINI_HOME=%PERFIL_ROOT%"
set "ANTIGRAVITY_GEMINI_DIR=%PERFIL_ROOT%\\.gemini"
set "ANTIGRAVITY_APP_DATA_DIR=%AGY_ORIG_HOME%\\.gemini\\antigravity-cli"

if not exist "%APPDATA%\\Antigravity" mkdir "%APPDATA%\\Antigravity" >nul 2>&1
if not exist "%LOCALAPPDATA%" mkdir "%LOCALAPPDATA%" >nul 2>&1
if not exist "%ANTIGRAVITY_GEMINI_DIR%" mkdir "%ANTIGRAVITY_GEMINI_DIR%" >nul 2>&1
if not exist "%ANTIGRAVITY_APP_DATA_DIR%" mkdir "%ANTIGRAVITY_APP_DATA_DIR%" >nul 2>&1

set "AGY_LAUNCH_ARGS="
set "AGY_LAUNCH_FILE=%TEMP%\\agy_launch_{name}_%RANDOM%%RANDOM%.cmd"
python "{script_path}" pre-run {name} "%AGY_LAUNCH_FILE%" %*
if errorlevel 3 goto :cleanup
if errorlevel 1 (
  echo [agy] ERRO no pre-run do perfil {name}. Abortado para nao misturar contas.
  goto :cleanup
)
if exist "%AGY_LAUNCH_FILE%" call "%AGY_LAUNCH_FILE%"
if defined AGY_LAUNCH_DRY_RUN (
  echo [dry-run] profile={name} cd=%CD% args=%AGY_LAUNCH_ARGS% %*
  goto :cleanup
)
"%~dp0agy.exe" %AGY_LAUNCH_ARGS% %*
python "{script_path}" post-run {name}
:cleanup
if exist "%AGY_LAUNCH_FILE%" del "%AGY_LAUNCH_FILE%" >nul 2>&1
endlocal
"""

def is_ntfs_junction(path):
    """Returns True if path exists and is an NTFS Directory Junction or reparse point."""
    if not os.path.exists(path):
        return False
    try:
        attrs = os.stat(path, follow_symlinks=False).st_file_attributes
        return bool(attrs & 0x0400)
    except Exception:
        return False

def create_directory_junction(junction_path, target_path):
    """Creates a Windows NTFS Directory Junction without requiring admin privileges."""
    cmd = f'cmd /c mklink /J "{junction_path}" "{target_path}"'
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return res.returncode == 0

def remove_directory_junction(junction_path):
    """Safely unlinks an NTFS junction using Windows rmdir without deleting target directory contents."""
    if is_ntfs_junction(junction_path):
        cmd = f'cmd /c rmdir "{junction_path}"'
        subprocess.run(cmd, shell=True, capture_output=True)
        return True
    return False

def ensure_shared_sessions(dry_run=False):
    """
    Ensures unified session storage across all profiles.
    Migrates conversation history, summaries DB, and brain assets from isolated profile(s)
    to ~/.gemini/antigravity-cli and links each profile's antigravity-cli directory via NTFS Junction.
    Keeps auth credentials (wincred.json, google_accounts.json, profile_identity.json) strictly isolated.
    """
    import sqlite3
    central_dir = os.path.join(USER_HOME, ".gemini", "antigravity-cli")
    c_convs = os.path.join(central_dir, "conversations")
    c_brain = os.path.join(central_dir, "brain")
    c_annot = os.path.join(central_dir, "annotations")
    c_hist = os.path.join(central_dir, "history.jsonl")
    c_db = os.path.join(central_dir, "conversation_summaries.db")

    if not dry_run:
        os.makedirs(c_convs, exist_ok=True)
        os.makedirs(c_brain, exist_ok=True)
        os.makedirs(c_annot, exist_ok=True)

    profiles = discover_profiles()
    for pname, prof in profiles.items():
        if prof.get("root") == USER_HOME:
            continue
        p_gemini = prof.get("gemini_dir")
        if not p_gemini:
            continue
        p_cli = os.path.join(p_gemini, "antigravity-cli")

        if is_ntfs_junction(p_cli):
            continue

        if os.path.exists(p_cli):
            p_db = os.path.join(p_cli, "conversation_summaries.db")
            if os.path.exists(p_db) and os.path.getsize(p_db) > 0 and os.path.exists(c_db) and not dry_run:
                try:
                    conn = sqlite3.connect(c_db)
                    cur = conn.cursor()
                    cur.execute(f"ATTACH DATABASE '{p_db}' AS p_db")
                    cur.execute("INSERT OR IGNORE INTO conversation_summaries SELECT * FROM p_db.conversation_summaries")
                    try:
                        cur.execute("INSERT OR IGNORE INTO conversations_fts SELECT * FROM p_db.conversations_fts")
                    except Exception:
                        pass
                    try:
                        cur.execute("INSERT OR IGNORE INTO conversation_parents SELECT * FROM p_db.conversation_parents")
                    except Exception:
                        pass
                    conn.commit()
                    cur.execute("DETACH DATABASE p_db")
                    conn.close()
                except Exception as e:
                    print(f"{YELLOW}[!] Aviso ao mesclar banco de {pname}: {e}{RESET}")

            # Copy conversations
            p_convs = os.path.join(p_cli, "conversations")
            if os.path.exists(p_convs) and not dry_run:
                for f in os.listdir(p_convs):
                    sf = os.path.join(p_convs, f)
                    df = os.path.join(c_convs, f)
                    if os.path.isfile(sf) and not os.path.exists(df):
                        try:
                            shutil.copy2(sf, df)
                        except Exception:
                            pass

            # Copy brain
            p_br = os.path.join(p_cli, "brain")
            if os.path.exists(p_br) and not dry_run:
                for item in os.listdir(p_br):
                    si = os.path.join(p_br, item)
                    di = os.path.join(c_brain, item)
                    if os.path.isdir(si) and not os.path.exists(di):
                        try:
                            shutil.copytree(si, di)
                        except Exception:
                            pass

            # Copy annotations
            p_an = os.path.join(p_cli, "annotations")
            if os.path.exists(p_an) and not dry_run:
                for f in os.listdir(p_an):
                    sf = os.path.join(p_an, f)
                    df = os.path.join(c_annot, f)
                    if os.path.isfile(sf) and not os.path.exists(df):
                        try:
                            shutil.copy2(sf, df)
                        except Exception:
                            pass

            # Merge history
            p_h = os.path.join(p_cli, "history.jsonl")
            if os.path.exists(p_h) and not dry_run:
                try:
                    c_lines = set()
                    if os.path.exists(c_hist):
                        with open(c_hist, "r", encoding="utf-8", errors="ignore") as f:
                            c_lines = set(f.read().splitlines())
                    with open(p_h, "r", encoding="utf-8", errors="ignore") as f:
                        new_lines = [l for l in f.read().splitlines() if l and l not in c_lines]
                    if new_lines:
                        with open(c_hist, "a", encoding="utf-8") as f:
                            for l in new_lines:
                                f.write(l + "\n")
                except Exception:
                    pass

            # Backup and replace with junction
            if not dry_run:
                backup_path = os.path.join(p_gemini, "antigravity-cli.pre-shared-backup")
                if os.path.exists(backup_path):
                    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
                    backup_path = f"{backup_path}-{ts}"
                try:
                    shutil.move(p_cli, backup_path)
                    create_directory_junction(p_cli, central_dir)
                except Exception as e:
                    print(f"{YELLOW}[!] Não foi possível criar junction para {pname}: {e}{RESET}")
        else:
            if not dry_run:
                os.makedirs(p_gemini, exist_ok=True)
                create_directory_junction(p_cli, central_dir)

    return True

def cmd_share_sessions():
    print(f"\n{BOLD}{CYAN}=== UNIFICAÇÃO DE SESSÕES & HISTÓRICO CROSS-PROFILE ==={RESET}")
    print(f"{GRAY}Centralizando conversations/, conversation_summaries.db e brain/ com junctions NTFS...{RESET}")
    ensure_shared_sessions()
    write_all_launchers()
    print(f"{GREEN}[✓] Sessões unificadas com sucesso! Todos os perfis compartilham conversas e /resume.{RESET}\n")

def write_all_launchers():
    """Regenerates canonical .cmd launchers for all profiles and removes stale .bat/agy.cmd in AGY_BIN_DIR."""
    ensure_shared_sessions()
    profiles = discover_profiles()
    if not os.path.exists(AGY_BIN_DIR):
        print(f"{YELLOW}[!] Diretório de binários não encontrado: {AGY_BIN_DIR}{RESET}")
        return False

    # Remove stale agy.cmd and agy*.bat (keep agy-profile.bat / agy-tray.bat)
    removed = []
    for fname in os.listdir(AGY_BIN_DIR):
        low = fname.lower()
        if low == "agy.cmd" or (low.startswith("agy") and low.endswith(".bat") and low not in ("agy-profile.bat", "agy-tray.bat")):
            fpath = os.path.join(AGY_BIN_DIR, fname)
            try:
                os.remove(fpath)
                removed.append(fname)
            except Exception as e:
                print(f"{YELLOW}[!] Não foi possível remover {fname}: {e}{RESET}")
    if removed:
        print(f"{GRAY}[*] Removidos launchers antigos: {', '.join(removed)}{RESET}")

    written = []
    for pname, prof in profiles.items():
        cname = get_launcher_filename(pname)
        content = generate_launcher_content(pname, prof["root"])
        cpath = os.path.join(AGY_BIN_DIR, cname)
        with open(cpath, "w", encoding="utf-8") as f:
            f.write(content)
        written.append(f"{cname} -> {pname}")
    print(f"{GREEN}[✓] Launchers atualizados em {AGY_BIN_DIR}:{RESET}")
    for w in written:
        print(f"    • {w}")
    return True

def sync_profile_to_config_and_launchers(name, email=None):
    """Ensures launcher (.cmd), widget_config.json, and quota cache are properly set for a profile."""
    prof_dir = os.path.join(PROFILES_BASE_DIR, name)
    gemini_dir = os.path.join(prof_dir, ".gemini")
    acc_email = email
    if not acc_email:
        acc_file = os.path.join(gemini_dir, "google_accounts.json")
        if os.path.exists(acc_file):
            try:
                with open(acc_file, "r", encoding="utf-8") as f:
                    acc_email = json.load(f).get("active", f"{name}@gmail.com")
            except Exception:
                acc_email = f"{name}@gmail.com"
        else:
            acc_email = f"{name}@gmail.com"

    # Create dedicated launcher script in AGY_BIN_DIR
    if os.path.exists(AGY_BIN_DIR):
        cname = get_launcher_filename(name)
        cmd_content = generate_launcher_content(name, prof_dir)
        try:
            with open(os.path.join(AGY_BIN_DIR, cname), "w", encoding="utf-8") as f:
                f.write(cmd_content)
        except Exception:
            pass

    # Sincroniza widget_config.json
    try:
        conf_file = os.path.join(CUSTOM_DIR, "widget_config.json")
        if os.path.exists(conf_file):
            with open(conf_file, "r", encoding="utf-8") as f:
                cdata = json.load(f)
            cdata.setdefault("enabled_profiles", {})[name] = True
            if "profile_order" in cdata and name not in cdata["profile_order"]:
                cdata["profile_order"].append(name)
            if "profile_models" in cdata and name not in cdata["profile_models"]:
                cdata["profile_models"][name] = [
                    "Gemini 3.8 Flash (High)",
                    "Claude Sonnet 4.6 (Thinking)",
                    "GPT-OSS 120B (Medium)"
                ]
            with open(conf_file, "w", encoding="utf-8") as f:
                json.dump(cdata, f, indent=2)
    except Exception:
        pass

    # Sincroniza cache de cotas
    try:
        q_file = os.path.join(CUSTOM_DIR, "profiles_quotas.json")
        qdata = {}
        if os.path.exists(q_file):
            with open(q_file, "r", encoding="utf-8") as f:
                qdata = json.load(f)
        if name not in qdata:
            qdata[name] = {
                "email": acc_email,
                "display": name.upper(),
                "has_oauth": False,
                "is_pro": False,
                "gemini_5h": {"used_pct": 0.0, "rem_pct": 100.0, "reset_in_seconds": 0},
                "gemini_7d": {"used_pct": 0.0, "rem_pct": 100.0, "reset_in_seconds": 0},
                "outros_3p": {"used_pct": 0.0, "rem_pct": 100.0, "reset_in_seconds": 0},
                "argon": None
            }
            with open(q_file, "w", encoding="utf-8") as f:
                json.dump(qdata, f, indent=2)
    except Exception:
        pass

def cmd_create(name, email=None):
    if not name:
        return False
    name = "".join(c for c in name if c.isalnum() or c in ("-", "_")).lower()

    profiles = discover_profiles()
    if name in profiles:
        print(f"{YELLOW}[!] Um perfil com o nome '{name}' já existe.{RESET}")
        sync_profile_to_config_and_launchers(name, email)
        return True

    prof_dir = os.path.join(PROFILES_BASE_DIR, name)
    gemini_dir = os.path.join(prof_dir, ".gemini")
    cli_dir = os.path.join(gemini_dir, "antigravity-cli")
    app_data = os.path.join(prof_dir, "AppData", "Roaming", "Antigravity")
    local_data = os.path.join(prof_dir, "AppData", "Local")

    os.makedirs(gemini_dir, exist_ok=True)
    os.makedirs(app_data, exist_ok=True)
    os.makedirs(local_data, exist_ok=True)
    c_app_data = os.path.join(USER_HOME, ".gemini", "antigravity-cli")
    if not is_ntfs_junction(cli_dir) and not os.path.exists(cli_dir):
        create_directory_junction(cli_dir, c_app_data)

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

    # Cria launchers e sincroniza widget_config.json e quotas
    sync_profile_to_config_and_launchers(name, acc_email)

    print(f"\n{BOLD}{GREEN}[✓] Perfil '{name}' criado com sucesso!{RESET}")
    print(f"    📁 Pasta: {prof_dir}")
    print(f"    👤 Email inicial: {acc_email}")
    print(f"\n{YELLOW}Próximo passo: Autentique a conta Google deste perfil:{RESET}")
    print(f"  {CYAN}agy-profile auth {name}{RESET}\n")
    return True

def cmd_delete(target, force=False):
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

    if chosen_key == "perfil1":
        print(f"{RED}[!] O perfil 'perfil1' é o perfil principal do sistema e não pode ser excluído.{RESET}")
        return False

    prof = profiles[chosen_key]
    prof_root = prof["root"]

    if not force:
        confirm = input(f"Tem certeza que deseja EXCLUIR permanentemente o perfil '{chosen_key}' ({prof['display']})? [s/N]: ").strip().lower()
        if confirm not in ("s", "sim", "y", "yes"):
            print("Operação cancelada.")
            return False

    # 1. Se for o perfil ativo, chaveia de volta para perfil1
    if get_active_profile() == chosen_key:
        print(f"{YELLOW}[*] O perfil '{chosen_key}' está ativo no momento. Alternando de volta para perfil1...{RESET}")
        cmd_switch("perfil1")

    # 2. Exclui arquivos .cmd no AGY_BIN_DIR
    if os.path.exists(AGY_BIN_DIR):
        cmd_candidates = [f"agy-{chosen_key}.cmd", f"agy-{chosen_key.lower()}.cmd"]
        if chosen_key.startswith("perfil") and chosen_key[6:].isdigit():
            cmd_candidates.append(f"agy{chosen_key[6:]}.cmd")
        elif chosen_key.isdigit():
            cmd_candidates.append(f"agy{chosen_key}.cmd")
        for cname in cmd_candidates:
            cpath = os.path.join(AGY_BIN_DIR, cname)
            if os.path.exists(cpath):
                try:
                    os.remove(cpath)
                except Exception:
                    pass

    # 3. Remove diretório da raiz do perfil
    p_cli = os.path.join(prof_root, ".gemini", "antigravity-cli")
    remove_directory_junction(p_cli)
    if os.path.exists(prof_root):
        try:
            shutil.rmtree(prof_root, ignore_errors=True)
        except Exception as e:
            print(f"{RED}[!] Erro ao remover diretório '{prof_root}': {e}{RESET}")

    # 4. Remove de widget_config.json
    widget_cfg_file = os.path.join(CUSTOM_DIR, "widget_config.json")
    if os.path.exists(widget_cfg_file):
        try:
            with open(widget_cfg_file, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            order = cfg.get("profile_order", [])
            if chosen_key in order:
                order.remove(chosen_key)
                cfg["profile_order"] = order
            if "enabled_profiles" in cfg:
                cfg["enabled_profiles"].pop(chosen_key, None)
            if "profile_nicknames" in cfg:
                cfg["profile_nicknames"].pop(chosen_key, None)
            if "profile_positions" in cfg:
                cfg["profile_positions"].pop(chosen_key, None)
            if "profile_models" in cfg:
                cfg["profile_models"].pop(chosen_key, None)
            if "pro_profiles" in cfg:
                cfg["pro_profiles"].pop(chosen_key, None)
            with open(widget_cfg_file, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass

    # 5. Remove de profiles_quotas.json
    if os.path.exists(QUOTAS_CACHE_FILE):
        try:
            with open(QUOTAS_CACHE_FILE, "r", encoding="utf-8") as f:
                qdata = json.load(f)
            if chosen_key in qdata:
                qdata.pop(chosen_key, None)
                with open(QUOTAS_CACHE_FILE, "w", encoding="utf-8") as f:
                    json.dump(qdata, f, indent=2)
        except Exception:
            pass

    print(f"\n{BOLD}{GREEN}[✓] Perfil '{chosen_key}' excluído com sucesso!{RESET}")
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
    print("  [0] Cancelar\n")

    opt = input("Opção [0-2]: ").strip()
    if opt == "1":
        oauth_script = os.path.join(os.path.dirname(__file__), "oauth_auth.py")
        subprocess.run([sys.executable, oauth_script, gem_dir])
        info = get_profile_info(prof)
        if info["email"] and info["email"] != "Desconhecido":
            set_profile_identity(chosen_key, info["email"], profiles)
        print(f"\n{GREEN}[✓] Concluído! Conta autenticada: {info['email']}{RESET}\n")
    elif opt == "2":
        cmd_desktop(chosen_key)
        print(f"{GREEN}[*] Após fazer login no Desktop, as credenciais serão salvas no perfil automaticamente.{RESET}\n")
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
        print(" [9] 🗑️  Excluir perfil (remover permanentemente)")
        print(" [L] 📂 Opções de inicialização (pasta/permissão)")
        print(" [0] ❌ Sair\n")

        choice = input("Escolha uma opção [0-9/L]: ").strip().lower()
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
        elif choice == "9":
            cmd_list()
            target = input("Número ou nome do perfil para EXCLUIR: ").strip()
            if target:
                cmd_delete(target)
        elif choice == "l":
            cmd_list()
            target = input("Número ou nome do perfil para configurar inicialização: ").strip()
            if target:
                cmd_launch("config", target)
        elif choice == "0":
            break
        else:
            print(f"{RED}Opção inválida.{RESET}")

# ─────────────────────────── WORKDIR / TRUSTED FOLDER ───────────────────────────

def load_workdirs():
    """Returns dict of {profile_name: [path, ...]}."""
    if os.path.exists(WORKDIRS_FILE):
        try:
            with open(WORKDIRS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_workdirs(data):
    os.makedirs(CUSTOM_DIR, exist_ok=True)
    with open(WORKDIRS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_workdir_for_profile(profile_name):
    """Returns the active (first) working dir for a profile, or None."""
    wds = load_workdirs()
    entry = wds.get(profile_name)
    if not entry:
        return None
    if isinstance(entry, list):
        return entry[0] if entry else None
    return entry  # plain string (legacy)

def print_workdir_path(profile_name):
    """Outputs only the working dir path (called by .cmd launchers)."""
    d = get_workdir_for_profile(profile_name)
    if d and os.path.isdir(d):
        print(d)
    else:
        print("")

def ensure_trusted_workspace(profile_name, path):
    """Adds path to trustedWorkspaces in the profile's antigravity-cli/settings.json."""
    if not path:
        return False
    profiles = discover_profiles()
    prof = profiles.get(profile_name)
    if not prof:
        return False
    cli_dir = os.path.join(prof["gemini_dir"], "antigravity-cli")
    settings_path = os.path.join(cli_dir, "settings.json")
    data = {}
    if os.path.exists(settings_path):
        try:
            with open(settings_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return False
        except Exception:
            # Skip writing if existing settings.json fails to parse
            return False
    trusted = data.get("trustedWorkspaces")
    if not isinstance(trusted, list):
        trusted = []
    norm = os.path.normpath(path)
    if not any(os.path.normpath(p).lower() == norm.lower() for p in trusted if isinstance(p, str)):
        trusted.append(norm)
        data["trustedWorkspaces"] = trusted
        os.makedirs(cli_dir, exist_ok=True)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    return True

def cmd_workdir_set(profile_name, path):
    """Sets a trusted folder as the default for a profile."""
    path = os.path.expandvars(os.path.expanduser(path.strip().strip('"').strip("'")))
    if not os.path.isdir(path):
        print(f"{YELLOW}[!] Diretório não encontrado: {path}{RESET}")
        create = input("Deseja criar este diretório? [s/N]: ").strip().lower()
        if create in ("s", "sim", "y", "yes"):
            os.makedirs(path, exist_ok=True)
            print(f"{GREEN}[✓] Diretório criado: {path}{RESET}")
        else:
            print("Operação cancelada.")
            return False

    wds = load_workdirs()
    entry = wds.get(profile_name, [])
    if isinstance(entry, str):
        entry = [entry]
    # Put the new path at front (default), remove duplicates
    if path in entry:
        entry.remove(path)
    entry.insert(0, path)
    wds[profile_name] = entry
    save_workdirs(wds)
    ensure_trusted_workspace(profile_name, path)
    print(f"\n{BOLD}{GREEN}[✓] Pasta de trabalho padrão definida para '{profile_name}':{RESET}")
    print(f"    📂 {CYAN}{path}{RESET}")
    print(f"\n{GRAY}Próxima vez que abrir '{profile_name}', o CLI iniciará nesta pasta.{RESET}\n")
    return True

def cmd_workdir_add(profile_name, path):
    """Adds a trusted folder to a profile's list."""
    path = os.path.expandvars(os.path.expanduser(path.strip().strip('"').strip("'")))
    if not os.path.isdir(path):
        print(f"{YELLOW}[!] Diretório não encontrado: {path}{RESET}")
        create = input("Deseja criar este diretório? [s/N]: ").strip().lower()
        if create in ("s", "sim", "y", "yes"):
            os.makedirs(path, exist_ok=True)
        else:
            print("Operação cancelada.")
            return False

    wds = load_workdirs()
    entry = wds.get(profile_name, [])
    if isinstance(entry, str):
        entry = [entry]
    if path not in entry:
        entry.append(path)
    wds[profile_name] = entry
    save_workdirs(wds)
    ensure_trusted_workspace(profile_name, path)
    print(f"{GREEN}[✓] '{path}' adicionado às pastas de '{profile_name}'.{RESET}")
    return True

def cmd_workdir_remove(profile_name, path=None):
    """Removes a trusted folder from a profile."""
    wds = load_workdirs()
    entry = wds.get(profile_name, [])
    if isinstance(entry, str):
        entry = [entry]

    if not entry:
        print(f"{YELLOW}[!] Nenhuma pasta configurada para '{profile_name}'.{RESET}")
        return False

    if path:
        path = os.path.expandvars(os.path.expanduser(path.strip().strip('"').strip("'")))
        if path in entry:
            entry.remove(path)
            wds[profile_name] = entry
            save_workdirs(wds)
            print(f"{GREEN}[✓] Pasta '{path}' removida de '{profile_name}'.{RESET}")
        else:
            print(f"{YELLOW}[!] Pasta '{path}' não encontrada na lista de '{profile_name}'.{RESET}")
    else:
        print(f"\n{BOLD}Pastas configuradas para '{profile_name}':{RESET}")
        for i, p in enumerate(entry, 1):
            print(f"  [{i}] {p}")
        choice = input("Número para remover (Enter para cancelar): ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(entry):
            removed = entry.pop(int(choice) - 1)
            wds[profile_name] = entry
            save_workdirs(wds)
            print(f"{GREEN}[✓] '{removed}' removida.{RESET}")
        else:
            print("Cancelado.")
    return True

def cmd_workdir_list(profile_name=None):
    """Lists trusted folders for one or all profiles."""
    wds = load_workdirs()
    if not wds:
        print(f"\n{YELLOW}[i] Nenhuma pasta de trabalho configurada ainda.{RESET}")
        print(f"    Use: {CYAN}agy-profile workdir set <perfil> <caminho>{RESET}\n")
        return

    targets = {profile_name: wds[profile_name]} if (profile_name and profile_name in wds) else wds
    print(f"\n{BOLD}{CYAN}📂 PASTAS DE TRABALHO CONFIGURADAS{RESET}\n")
    for pname, entry in targets.items():
        dirs = entry if isinstance(entry, list) else [entry]
        print(f"  {BOLD}{WHITE}{pname}{RESET}")
        for i, d in enumerate(dirs):
            tag = f"  {GREEN}← padrão{RESET}" if i == 0 else ""
            exists_tag = "" if os.path.isdir(d) else f"  {RED}[não encontrado]{RESET}"
            print(f"    [{i+1}] {d}{tag}{exists_tag}")
    print()

def cmd_workdir_choose(profile_name):
    """Interactive: pick which saved folder to open (called on CLI launch if no default)."""
    wds = load_workdirs()
    entry = wds.get(profile_name, [])
    if isinstance(entry, str):
        entry = [entry]

    if not entry:
        print(f"\n{YELLOW}[i] Nenhuma pasta configurada para '{profile_name}'.{RESET}")
        new_path = input(f"Digite o caminho da pasta (Enter para usar o atual '{os.getcwd()}'): ").strip()
        if not new_path:
            new_path = os.getcwd()
        cmd_workdir_set(profile_name, new_path)
        return new_path

    print(f"\n{BOLD}{CYAN}📂 Escolha a pasta de trabalho para '{profile_name}':{RESET}\n")
    for i, d in enumerate(entry, 1):
        exists_tag = "" if os.path.isdir(d) else f"  {RED}(não encontrado){RESET}"
        default_tag = f"  {GREEN}← padrão{RESET}" if i == 1 else ""
        print(f"  [{i}] {d}{default_tag}{exists_tag}")
    print(f"  [N] Adicionar nova pasta")
    print(f"  [Enter] Usar padrão: {CYAN}{entry[0]}{RESET}\n")

    choice = input("Opção: ").strip().lower()
    if choice == "" or choice == "1":
        return entry[0]
    elif choice == "n":
        new_path = input("Novo caminho: ").strip()
        if new_path:
            cmd_workdir_set(profile_name, new_path)
            return new_path
    elif choice.isdigit() and 1 <= int(choice) <= len(entry):
        selected = entry[int(choice) - 1]
        # Promote to default
        entry.remove(selected)
        entry.insert(0, selected)
        wds[profile_name] = entry
        save_workdirs(wds)
        return selected
    return entry[0]

# ─────────────────────────── LAUNCH OPTIONS & PERMISSIONS ───────────────────────

PERMISSION_PRESETS = {
    "default": ("Padrão (pergunta antes de cada ação)", []),
    "accept-edits": ("Aceitar edições automaticamente", ["--mode", "accept-edits"]),
    "auto": ("Automático", ["--mode", "auto"]),
    "plan": ("Somente planejar", ["--mode", "plan"]),
    "all": ("TODAS AS PERMISSÕES (--dangerously-skip-permissions)", ["--dangerously-skip-permissions"]),
    "sandbox": ("Sandbox (terminal restrito)", ["--sandbox"]),
}

PERMISSION_ALIASES = {
    "todas": "all",
    "all-permissions": "all",
    "all_permissions": "all",
    "skip": "all",
    "dangerously-skip-permissions": "all",
    "padrao": "default",
    "padrão": "default",
    "normal": "default",
    "edits": "accept-edits",
    "accept": "accept-edits",
    "plano": "plan",
}

def normalize_permission(perm):
    if not perm:
        return "default"
    k = perm.strip().lower()
    k = PERMISSION_ALIASES.get(k, k)
    return k if k in PERMISSION_PRESETS else None

def load_launch_config():
    if os.path.exists(LAUNCH_FILE):
        try:
            with open(LAUNCH_FILE, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d if isinstance(d, dict) else {}
        except Exception:
            pass
    return {}

def save_launch_config(data):
    os.makedirs(CUSTOM_DIR, exist_ok=True)
    with open(LAUNCH_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_profile_launch_opts(profile_name):
    cfg = load_launch_config()
    entry = cfg.get(profile_name, {})
    if not isinstance(entry, dict):
        entry = {}
    perm = normalize_permission(entry.get("permission", "default")) or "default"
    ask = entry.get("ask_on_launch", True)
    return {"permission": perm, "ask_on_launch": bool(ask)}

def set_profile_launch_opts(profile_name, permission=None, ask_on_launch=None):
    cfg = load_launch_config()
    entry = cfg.get(profile_name, {})
    if not isinstance(entry, dict):
        entry = {}
    if permission is not None:
        norm = normalize_permission(permission)
        if not norm:
            return False
        entry["permission"] = norm
    else:
        entry.setdefault("permission", "default")
    if ask_on_launch is not None:
        entry["ask_on_launch"] = bool(ask_on_launch)
    else:
        entry.setdefault("ask_on_launch", True)
    cfg[profile_name] = entry
    save_launch_config(cfg)
    return True

def build_agy_args(permission, user_args):
    """Returns preset agy CLI flags unless user already passed overriding flags."""
    uargs = list(user_args or [])
    for a in uargs:
        if a in ("--dangerously-skip-permissions", "--mode", "--sandbox") or a.startswith("--mode="):
            return []
    key = normalize_permission(permission) or "default"
    return list(PERMISSION_PRESETS[key][1])

def write_launch_file(path, workdir, args):
    """Writes temporary .cmd helper setting cd and AGY_LAUNCH_ARGS for the launcher."""
    lines = ["@echo off"]
    if workdir and os.path.isdir(workdir):
        lines.append(f'cd /d "{workdir}"')
    args_str = " ".join(args or [])
    lines.append(f'set "AGY_LAUNCH_ARGS={args_str}"')
    content = "\r\n".join(lines) + "\r\n"

    enc = "mbcs"
    try:
        cp = ctypes.windll.kernel32.GetConsoleOutputCP()
        if cp:
            enc = f"cp{cp}"
    except Exception:
        enc = "mbcs"

    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding=enc, errors="replace") as f:
        f.write(content)

def _pick_folder_submenu(profile_name, current_workdir):
    wds = load_workdirs()
    entry = wds.get(profile_name, [])
    if isinstance(entry, str):
        entry = [entry]
    print(f"\n{BOLD}{CYAN}📂 Selecionar pasta de trabalho para '{profile_name}':{RESET}")
    for i, d in enumerate(entry, 1):
        tag = f"  {GREEN}← salva{RESET}" if i == 1 else ""
        exists_tag = "" if os.path.isdir(d) else f"  {RED}[não encontrado]{RESET}"
        print(f"  [{i}] {d}{tag}{exists_tag}")
    print(f"  [A] Usar pasta atual ({os.getcwd()})")
    print(f"  [N] Digitar novo caminho")
    print(f"  [0] Voltar\n")
    ch = input("Opção: ").strip()
    low = ch.lower()
    if low == "0" or low == "":
        return current_workdir
    if low == "a":
        p = os.getcwd()
        ensure_trusted_workspace(profile_name, p)
        return p
    if low == "n":
        new_p = input("Novo caminho da pasta: ").strip().strip('"').strip("'")
        if not new_p:
            return current_workdir
        new_p = os.path.expandvars(os.path.expanduser(new_p))
        if not os.path.isdir(new_p):
            cr = input(f"{YELLOW}Diretório não existe ({new_p}). Criar? [s/N]: {RESET}").strip().lower()
            if cr in ("s", "sim", "y", "yes"):
                os.makedirs(new_p, exist_ok=True)
            else:
                return current_workdir
        sv = input("Salvar esta pasta na lista do perfil? [S/n]: ").strip().lower()
        if sv in ("", "s", "sim", "y", "yes"):
            cmd_workdir_add(profile_name, new_p)
        else:
            ensure_trusted_workspace(profile_name, new_p)
        return new_p
    if ch.isdigit() and 1 <= int(ch) <= len(entry):
        sel = entry[int(ch) - 1]
        if os.path.isdir(sel):
            ensure_trusted_workspace(profile_name, sel)
            return sel
        print(f"{RED}[!] Diretório não encontrado: {sel}{RESET}")
    return current_workdir

def _pick_permission_submenu(current_permission):
    keys = list(PERMISSION_PRESETS.keys())
    print(f"\n{BOLD}{CYAN}🔐 Selecionar modo de permissão:{RESET}")
    for i, k in enumerate(keys, 1):
        label, _ = PERMISSION_PRESETS[k]
        mark = f" {GREEN}← atual{RESET}" if k == current_permission else ""
        print(f"  [{i}] {k:<13} - {label}{mark}")
    print("  [0] Voltar\n")
    ch = input("Opção: ").strip()
    if ch.isdigit() and 1 <= int(ch) <= len(keys):
        return keys[int(ch) - 1]
    norm = normalize_permission(ch)
    if norm:
        return norm
    return current_permission

def launch_picker(profile_name, email, workdir, permission, save_only=False):
    """Interactive pre-launch screen for choosing folder and permission mode."""
    cur_wd = workdir
    cur_perm = normalize_permission(permission) or "default"
    while True:
        wd_disp = cur_wd if (cur_wd and os.path.isdir(cur_wd)) else "(pasta atual)"
        perm_label = PERMISSION_PRESETS.get(cur_perm, PERMISSION_PRESETS["default"])[0]
        print(f"\n{BOLD}{CYAN}🚀 {profile_name.upper()}{RESET} · {WHITE}{email}{RESET}")
        print(f"📂 Pasta:     {CYAN}{wd_disp}{RESET}")
        print(f"🔐 Permissão: {YELLOW}{perm_label}{RESET}")
        if save_only:
            print(f"{GRAY}[Enter] Salvar e sair  [P] Pasta  [M] Permissão  [0] Cancelar{RESET}")
        else:
            print(f"{GRAY}[Enter] Abrir  [P] Pasta  [M] Permissão  [S] Salvar como padrão  [D] Não perguntar mais  [0] Cancelar{RESET}")
        ch = input("> ").strip().lower()
        if ch == "":
            if save_only:
                if cur_wd and os.path.isdir(cur_wd):
                    cmd_workdir_set(profile_name, cur_wd)
                set_profile_launch_opts(profile_name, permission=cur_perm)
                print(f"{GREEN}[✓] Configurações salvas para '{profile_name}'.{RESET}")
            return (cur_wd, cur_perm)
        elif ch == "p":
            cur_wd = _pick_folder_submenu(profile_name, cur_wd)
        elif ch == "m":
            cur_perm = _pick_permission_submenu(cur_perm)
        elif ch == "s":
            if cur_wd and os.path.isdir(cur_wd):
                cmd_workdir_set(profile_name, cur_wd)
            set_profile_launch_opts(profile_name, permission=cur_perm)
            print(f"{GREEN}[✓] Definido como padrão para '{profile_name}'!{RESET}")
            if save_only:
                return (cur_wd, cur_perm)
        elif ch == "d" and not save_only:
            set_profile_launch_opts(profile_name, permission=cur_perm, ask_on_launch=False)
            print(f"{GRAY}[i] Pergunta ao abrir desativada para '{profile_name}' (reative com: agy-profile launch ask {profile_name} on).{RESET}")
            return (cur_wd, cur_perm)
        elif ch == "0":
            return None
        else:
            print(f"{YELLOW}Opção inválida.{RESET}")

# ─────────────────────────── DOCTOR / IDENTITY / RESET ─────────────────────────

def resolve_profile_key(target, profiles=None):
    if profiles is None:
        profiles = discover_profiles()
    if not target:
        return None
    if target.isdigit():
        idx = int(target)
        keys = list(profiles.keys())
        if 1 <= idx <= len(keys):
            return keys[idx - 1]
    for k in profiles.keys():
        if k.lower() == target.lower():
            return k
    return None

def cmd_reset_auth(target, force=False):
    """Quarantines all credential/identity files of a profile without touching Windows Credential Manager."""
    profiles = discover_profiles()
    chosen = resolve_profile_key(target, profiles)
    if not chosen:
        print(f"{RED}[!] Perfil '{target}' não encontrado.{RESET}")
        return False
    gem_dir = profiles[chosen]["gemini_dir"]
    if not force:
        ans = input(f"{YELLOW}[?] Limpar credenciais e identidade salvos de '{chosen}'? [s/N]: {RESET}").strip().lower()
        if ans not in ("s", "sim", "y", "yes"):
            print("Cancelado.")
            return False
    moved = []
    for fname in ("wincred.json", "oauth_creds.json", "google_accounts.json", IDENTITY_FILE, SESSION_MARKER):
        fpath = os.path.join(gem_dir, fname)
        if os.path.exists(fpath):
            q = _quarantine(fpath)
            if q:
                moved.append(os.path.basename(q))
    if moved:
        print(f"{GREEN}[✓] Auth resetado para '{chosen}'. Arquivos em quarentena: {', '.join(moved)}{RESET}")
    else:
        print(f"{GRAY}[*] '{chosen}' já estava sem credenciais salvas.{RESET}")
    return True

def cmd_bind(target, email):
    """Manually binds a profile to a canonical Google email."""
    profiles = discover_profiles()
    chosen = resolve_profile_key(target, profiles)
    if not chosen:
        print(f"{RED}[!] Perfil '{target}' não encontrado.{RESET}")
        return False
    if not email or "@" not in email:
        print(f"{RED}[!] Email inválido: {email}{RESET}")
        return False
    set_profile_identity(chosen, email.strip(), profiles)
    print(f"{GREEN}[✓] Perfil '{chosen}' vinculado à identidade: {CYAN}{email.strip()}{RESET}")
    return True

def cmd_capture(target, force=False):
    """Saves the currently live Windows Credential Manager token into target profile."""
    profiles = discover_profiles()
    chosen = resolve_profile_key(target, profiles)
    if not chosen:
        print(f"{RED}[!] Perfil '{target}' não encontrado.{RESET}")
        return False
    cred = read_wincred()
    if not _valid_cred(cred):
        print(f"{RED}[!] Nenhuma credencial válida ativa no Gerenciador de Credenciais do Windows.{RESET}")
        return False
    email = cred.get("id_token_email")
    identity = get_profile_identity(chosen, profiles)
    if identity and identity.lower() != email.lower():
        print(f"{RED}[!] Recusado: '{chosen}' tem identidade '{identity}', mas a credencial ativa é '{email}'.{RESET}")
        print(f"{GRAY}    Use 'agy-profile reset-auth {chosen}' antes se quiser trocar a conta.{RESET}")
        return False
    if not force:
        ans = input(f"Capturar sessão ativa ({CYAN}{email}{RESET}) para o perfil '{chosen}'? [s/N]: ").strip().lower()
        if ans not in ("s", "sim", "y", "yes"):
            print("Cancelado.")
            return False
    gem_dir = profiles[chosen]["gemini_dir"]
    os.makedirs(gem_dir, exist_ok=True)
    with open(os.path.join(gem_dir, "wincred.json"), "w", encoding="utf-8") as f:
        json.dump(cred, f, indent=2)
    with open(os.path.join(gem_dir, "google_accounts.json"), "w", encoding="utf-8") as f:
        json.dump({"active": email, "old": []}, f, indent=2)
    if not identity:
        set_profile_identity(chosen, email, profiles)
    print(f"{GREEN}[✓] Credencial ({email}) capturada e vinculada a '{chosen}'.{RESET}")
    return True

def cmd_doctor(fix=False):
    """Audits all profiles for credential conflicts and auto-binds unique identities."""
    profiles = discover_profiles()
    rows = []
    wincred_owners = {}
    for pname, prof in profiles.items():
        gdir = prof["gemini_dir"]
        wfile = os.path.join(gdir, "wincred.json")
        afile = os.path.join(gdir, "google_accounts.json")
        w_email = None
        if os.path.exists(wfile):
            try:
                with open(wfile, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    if _valid_cred(d):
                        w_email = d.get("id_token_email")
            except Exception:
                pass
        a_email = None
        if os.path.exists(afile):
            try:
                with open(afile, "r", encoding="utf-8") as f:
                    a_email = json.load(f).get("active")
            except Exception:
                pass
        ident = get_profile_identity(pname, profiles)
        if w_email:
            wincred_owners.setdefault(w_email.lower(), []).append(pname)
        rows.append({
            "name": pname,
            "wincred": w_email,
            "identity": ident,
            "accounts": a_email,
        })

    # Non-destructive auto-bind for unique wincred emails with no identity yet
    auto_bound = []
    for r in rows:
        we = r["wincred"]
        if we and not r["identity"] and len(wincred_owners.get(we.lower(), [])) == 1:
            set_profile_identity(r["name"], we, profiles)
            r["identity"] = we
            auto_bound.append(f"{r['name']}={we}")

    # Detect duplicate groups across wincred or identity
    dup_groups = {}
    for r in rows:
        key_email = (r["wincred"] or r["identity"] or "").lower()
        if key_email:
            dup_groups.setdefault(key_email, []).append(r["name"])

    print(f"\n{BOLD}{CYAN}🩺 DIAGNÓSTICO DE ISOLAMENTO DE PERFIS (doctor){RESET}\n")
    print(f"  {'PERFIL':<10} {'WINCRED':<28} {'IDENTIDADE':<28} {'GOOGLE_ACC':<28} STATUS")
    print(f"  {'-'*10} {'-'*28} {'-'*28} {'-'*28} {'-'*18}")
    conflicts = 0
    for r in rows:
        we = r["wincred"] or "-"
        ide = r["identity"] or "-"
        ae = r["accounts"] or "-"
        key_email = (r["wincred"] or r["identity"] or "").lower()
        is_dup = bool(key_email and len(dup_groups.get(key_email, [])) > 1)
        if is_dup:
            status = f"{RED}CONFLITO ({', '.join(dup_groups[key_email])}){RESET}"
            conflicts += 1
        elif r["wincred"] and r["identity"] and r["wincred"].lower() != r["identity"].lower():
            status = f"{RED}CONFLITO (ident!=wincred){RESET}"
            conflicts += 1
        elif r["wincred"] or r["identity"]:
            status = f"{GREEN}OK{RESET}"
        else:
            status = f"{YELLOW}sem conta{RESET}"
        print(f"  {r['name']:<10} {we:<28} {ide:<28} {ae:<28} {status}")
    print()
    if auto_bound:
        print(f"{CYAN}[i] Identidade vinculada automaticamente (únicas): {', '.join(auto_bound)}{RESET}")

    if fix and conflicts:
        for email_low, pnames in list(dup_groups.items()):
            if len(pnames) <= 1:
                continue
            print(f"\n{YELLOW}[!] Conta duplicada '{email_low}' encontrada em: {', '.join(pnames)}{RESET}")
            for i, pn in enumerate(pnames, 1):
                print(f"  [{i}] {pn}")
            ans = input("Qual perfil é o DONO legítimo desta conta? (número, Enter para pular): ").strip()
            if ans.isdigit() and 1 <= int(ans) <= len(pnames):
                owner = pnames[int(ans) - 1]
                set_profile_identity(owner, email_low, profiles)
                for pn in pnames:
                    if pn != owner:
                        cmd_reset_auth(pn, force=True)
    elif conflicts:
        print(f"{YELLOW}Use 'agy-profile doctor --fix' ou 'agy-profile reset-auth <perfil>' para resolver conflitos.{RESET}\n")
    return conflicts == 0

def cmd_launch(action, arg1=None, arg2=None):
    profiles = discover_profiles()
    if action == "show":
        targets = [resolve_profile_key(arg1, profiles)] if arg1 else list(profiles.keys())
        targets = [t for t in targets if t]
        if not targets:
            print(f"{RED}[!] Perfil não encontrado.{RESET}")
            return False
        print(f"\n{BOLD}{CYAN}🚀 CONFIGURAÇÕES DE INICIALIZAÇÃO{RESET}\n")
        for pname in targets:
            opts = get_profile_launch_opts(pname)
            wd = get_workdir_for_profile(pname) or "(pasta atual)"
            perm = opts["permission"]
            plabel = PERMISSION_PRESETS.get(perm, PERMISSION_PRESETS["default"])[0]
            ask_s = "Sim (abre seletor)" if opts["ask_on_launch"] else "Não (direto)"
            print(f"  {BOLD}{WHITE}{pname}{RESET}")
            print(f"    📂 Pasta padrão:    {CYAN}{wd}{RESET}")
            print(f"    🔐 Permissão:       {YELLOW}{perm}{RESET} — {plabel}")
            print(f"    ❓ Perguntar:       {ask_s}")
        print()
        return True
    elif action == "perm":
        chosen = resolve_profile_key(arg1 or get_active_profile(), profiles)
        if not chosen:
            print(f"{RED}[!] Perfil '{arg1}' não encontrado.{RESET}")
            return False
        norm = normalize_permission(arg2)
        if not norm:
            print(f"{RED}[!] Permissão inválida: '{arg2}'{RESET}")
            print(f"Opções válidas: {', '.join(PERMISSION_PRESETS.keys())}")
            return False
        set_profile_launch_opts(chosen, permission=norm)
        print(f"{GREEN}[✓] Permissão padrão de '{chosen}' definida para: {norm} ({PERMISSION_PRESETS[norm][0]}){RESET}")
        return True
    elif action == "ask":
        chosen = resolve_profile_key(arg1 or get_active_profile(), profiles)
        if not chosen:
            print(f"{RED}[!] Perfil '{arg1}' não encontrado.{RESET}")
            return False
        enable = (arg2 or "on").lower() in ("on", "1", "true", "sim", "s", "yes", "enable")
        set_profile_launch_opts(chosen, ask_on_launch=enable)
        state = "ATIVADO" if enable else "DESATIVADO"
        print(f"{GREEN}[✓] Seletor ao abrir '{chosen}': {state}{RESET}")
        return True
    elif action == "config":
        chosen = resolve_profile_key(arg1 or get_active_profile(), profiles)
        if not chosen:
            print(f"{RED}[!] Perfil '{arg1}' não encontrado.{RESET}")
            return False
        info = get_profile_info(profiles[chosen])
        wd = get_workdir_for_profile(chosen)
        opts = get_profile_launch_opts(chosen)
        res = launch_picker(chosen, info.get("email", "sem conta"), wd, opts["permission"], save_only=True)
        return res is not None
    else:
        print("Uso: agy-profile launch <show|perm|ask|config> [perfil] [valor]")
        return False

# ──────────────────────────────────────────────────────────────────────────────

def main():
    if len(sys.argv) == 1:
        interactive_menu()
        return

    subcmd = sys.argv[1].lower()
    if subcmd in ("pre-run", "prerun"):
        target = sys.argv[2] if len(sys.argv) > 2 else get_active_profile()
        launch_file = None
        user_args = []
        if len(sys.argv) > 3:
            if sys.argv[3].lower().endswith(".cmd"):
                launch_file = sys.argv[3]
                user_args = sys.argv[4:]
            else:
                user_args = sys.argv[3:]
        res = pre_run(target, launch_file=launch_file, user_args=user_args)
        if res == "cancel":
            sys.exit(3)
    elif subcmd in ("post-run", "postrun"):
        target = sys.argv[2] if len(sys.argv) > 2 else get_active_profile()
        post_run(target)
    elif subcmd in ("list", "quota", "quotas", "status", "ls"):
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
    elif subcmd in ("delete", "remove", "del", "rm"):
        if len(sys.argv) > 2:
            cmd_delete(sys.argv[2], force=False)
        else:
            cmd_list()
            target = input("Número ou nome do perfil para EXCLUIR: ").strip()
            if target:
                cmd_delete(target)
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
    elif subcmd in ("tray", "widget"):
        cmd_tray()
    elif subcmd in ("autostart", "startup"):
        enable = True
        if len(sys.argv) > 2:
            enable = sys.argv[2].lower() in ("on", "1", "true", "enable", "sim", "s")
        cmd_autostart(enable)
    elif subcmd == "doctor":
        fix_flag = "--fix" in [a.lower() for a in sys.argv[2:]]
        cmd_doctor(fix=fix_flag)
    elif subcmd in ("reset-auth", "logout", "reset"):
        if len(sys.argv) > 2:
            force_flag = "--yes" in sys.argv[2:] or "-y" in sys.argv[2:]
            target = next((a for a in sys.argv[2:] if not a.startswith("-")), None)
            if target:
                cmd_reset_auth(target, force=force_flag)
        else:
            print("Uso: agy-profile reset-auth <perfil> [--yes]")
    elif subcmd == "bind":
        if len(sys.argv) > 3:
            cmd_bind(sys.argv[2], sys.argv[3])
        else:
            print("Uso: agy-profile bind <perfil> <email>")
    elif subcmd == "capture":
        if len(sys.argv) > 2:
            force_flag = "--yes" in sys.argv[2:] or "-y" in sys.argv[2:]
            target = next((a for a in sys.argv[2:] if not a.startswith("-")), None)
            if target:
                cmd_capture(target, force=force_flag)
        else:
            print("Uso: agy-profile capture <perfil> [--yes]")
    elif subcmd == "launchers":
        write_all_launchers()
    elif subcmd in ("share-sessions", "unify-sessions", "migrate-sessions"):
        cmd_share_sessions()
    elif subcmd == "launch":
        action = sys.argv[2].lower() if len(sys.argv) > 2 else "show"
        arg1 = sys.argv[3] if len(sys.argv) > 3 else None
        arg2 = sys.argv[4] if len(sys.argv) > 4 else None
        cmd_launch(action, arg1, arg2)
    elif subcmd in ("perm", "permission", "permissao"):
        if len(sys.argv) > 3:
            cmd_launch("perm", sys.argv[2], sys.argv[3])
        elif len(sys.argv) > 2:
            cmd_launch("perm", get_active_profile(), sys.argv[2])
        else:
            cmd_launch("show")
    elif subcmd in ("workdir", "dir", "folder", "trusted", "setdir"):
        # agy-profile workdir set <profile> <path>
        # agy-profile workdir add <profile> <path>
        # agy-profile workdir remove <profile> [path]
        # agy-profile workdir list [profile]
        # agy-profile workdir choose <profile>
        # agy-profile workdir get <profile>   (outputs path only, for .cmd launchers)
        action = sys.argv[2].lower() if len(sys.argv) > 2 else "list"
        if action in ("set", "define", "default", "setdir"):
            profile_arg = sys.argv[3] if len(sys.argv) > 3 else get_active_profile()
            path_arg = sys.argv[4] if len(sys.argv) > 4 else None
            if not path_arg:
                print(f"Pasta atual (Enter para usar): {os.getcwd()}")
                path_arg = input("Caminho da pasta: ").strip() or os.getcwd()
            cmd_workdir_set(profile_arg, path_arg)
        elif action == "add":
            profile_arg = sys.argv[3] if len(sys.argv) > 3 else get_active_profile()
            path_arg = sys.argv[4] if len(sys.argv) > 4 else input("Caminho da pasta: ").strip()
            cmd_workdir_add(profile_arg, path_arg)
        elif action in ("remove", "rm", "del"):
            profile_arg = sys.argv[3] if len(sys.argv) > 3 else get_active_profile()
            path_arg = sys.argv[4] if len(sys.argv) > 4 else None
            cmd_workdir_remove(profile_arg, path_arg)
        elif action == "list":
            profile_arg = sys.argv[3] if len(sys.argv) > 3 else None
            cmd_workdir_list(profile_arg)
        elif action == "choose":
            profile_arg = sys.argv[3] if len(sys.argv) > 3 else get_active_profile()
            result = cmd_workdir_choose(profile_arg)
            if result:
                print(f"Pasta selecionada: {result}")
        elif action == "get":
            profile_arg = sys.argv[3] if len(sys.argv) > 3 else get_active_profile()
            print_workdir_path(profile_arg)
        else:
            # treat action as profile name, path as next arg
            if len(sys.argv) > 3:
                cmd_workdir_set(action, sys.argv[3])
            else:
                cmd_workdir_list(action)
    else:
        print(f"Comando desconhecido: {subcmd}")
        print("Comandos disponíveis: list, switch, create, delete, auth, desktop, run, tray, autostart, workdir, launch, perm, doctor, reset-auth, bind, capture, launchers")

if __name__ == "__main__":
    main()

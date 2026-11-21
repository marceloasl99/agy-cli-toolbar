import sys
import json
import datetime
import os
import platform

# Ensure full UTF-8 support on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CUSTOM_DIR = os.path.join(os.path.expanduser("~"), ".antigravity-custom")
SESSION_FILE = os.path.join(CUSTOM_DIR, ".session_time.json")
CONFIG_FILE = os.path.join(CUSTOM_DIR, "config.json")
LOG_FILE = os.path.join(CUSTOM_DIR, "statusline.log")

DEFAULT_CONFIG = {
    "theme": "default",           # "default", "tokyo_night", "catppuccin", "nord", "cyberpunk", "plain"
    "nerd_fonts": False,          # Enable for Nerd Font icons
    "smooth_bars": True,          # Sub-character smooth rendering for progress bars
    "show_line3": True,           # 3-line layout (Line 3: System Health, MCP, Git, Workspace, Clock)
    "show_cost": True,            # Estimated API cost & context cache savings
    "show_tokens_per_sec": True,  # Generation speed (tokens/sec)
    "show_quota_5h": True,        # 5-hour rolling quota gauge & countdown
    "show_quota_weekly": True,    # 7-day weekly quota gauge & countdown
    "show_burn_rate": True,       # Quota velocity / pace indicator
    "show_subagents": True,       # Active autonomous subagent swarm counter
    "show_tasks": True,           # Background async tasks counter
    "show_artifacts": True,       # Created artifacts / documents counter
    "show_email": True,           # User account and plan tier
    "show_profile": True,         # Active Google profile indicator
    "show_ram": True,             # Host RAM memory utilization
    "show_workspace": True,       # Project folder name
    "show_git": True,             # VCS branch, dirty indicator & diff stats
    "show_mcp": True,             # Active MCP servers count
    "show_skills": True,          # Registered skills count
    "show_sandbox": True,         # Security sandbox status
    "show_clock": True,           # Real-time local clock
    "show_version": True,         # CLI engine and runtime version
    "max_cached_sessions": 50
}

def load_config():
    conf = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_conf = json.load(f)
                conf.update(user_conf)
        except Exception:
            pass
    return conf

def debug_log(msg):
    if os.environ.get("STATUSLINE_DEBUG") == "1":
        try:
            with open(LOG_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{datetime.datetime.now().isoformat()}] {msg}\n")
        except Exception:
            pass

def format_tokens(num):
    if not num:
        return "0"
    if num >= 1_000_000:
        return f"{num / 1_000_000:.2f}M"
    if num >= 1_000:
        return f"{num / 1_000:.1f}k"
    return str(num)

def format_seconds(seconds):
    if not seconds or seconds <= 0:
        return "0m"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    if hours > 0:
        return f"{hours}h{minutes:02d}m"
    return f"{minutes}m"

def get_session_info(session_id, max_cached=50):
    now = datetime.datetime.now()
    if not session_id:
        return now.strftime("%H:%M:%S"), "0m", 0
    
    session_data = {}
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r", encoding="utf-8") as f:
                session_data = json.load(f)
        except Exception:
            session_data = {}

    start_iso = session_data.get(session_id)
    if start_iso:
        try:
            start_dt = datetime.datetime.fromisoformat(start_iso)
            elapsed_sec = max(int((now - start_dt).total_seconds()), 1)
            elapsed_str = format_seconds(elapsed_sec)
            return start_dt.strftime("%H:%M:%S"), elapsed_str, elapsed_sec
        except Exception:
            pass
    
    # Prune old sessions if list exceeds threshold
    if len(session_data) > max_cached:
        keys = list(session_data.keys())
        for k in keys[:-max_cached]:
            session_data.pop(k, None)

    session_data[session_id] = now.isoformat()
    try:
        os.makedirs(CUSTOM_DIR, exist_ok=True)
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session_data, f)
    except Exception:
        pass
    return now.strftime("%H:%M:%S"), "0m", 0

def get_system_ram():
    """Returns (used_percentage, total_gb_str) with pure Python standard library."""
    try:
        if sys.platform == "win32":
            import ctypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ('dwLength', ctypes.c_ulong),
                    ('dwMemoryLoad', ctypes.c_ulong),
                    ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong),
                    ('ullTotalPageFile', ctypes.c_ulonglong),
                    ('ullAvailPageFile', ctypes.c_ulonglong),
                    ('ullTotalVirtual', ctypes.c_ulonglong),
                    ('ullAvailVirtual', ctypes.c_ulonglong),
                    ('sullAvailExtendedVirtual', ctypes.c_ulonglong),
                ]
            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                total_gb = stat.ullTotalPhys / (1024 ** 3)
                return int(stat.dwMemoryLoad), f"{total_gb:.0f}G"
        elif sys.platform.startswith("linux") and os.path.exists("/proc/meminfo"):
            mem = {}
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        mem[parts[0].strip()] = int(parts[1].split()[0])
            total_kb = mem.get("MemTotal", 0)
            avail_kb = mem.get("MemAvailable", mem.get("MemFree", 0))
            if total_kb > 0:
                used_pct = int(((total_kb - avail_kb) / total_kb) * 100)
                total_gb = total_kb / (1024 * 1024)
                return used_pct, f"{total_gb:.0f}G"
    except Exception:
        pass
    return None, None

def get_git_branch_fast(repo_dir):
    """Fast .git/HEAD read in pure Python without spawning subprocesses."""
    try:
        if not repo_dir or not os.path.exists(repo_dir):
            return ""
        head_path = os.path.join(repo_dir, ".git", "HEAD")
        if os.path.isfile(head_path):
            with open(head_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if content.startswith("ref: refs/heads/"):
                    return content[16:]
                return content[:7]
    except Exception:
        pass
    return ""

def get_theme_colors(theme_name):
    if os.environ.get("NO_COLOR"):
        return {k: "" for k in [
            "CYAN_BG", "GREEN_BG", "YELLOW_BG", "MAGENTA_BG", "RED_BG", "BLUE_BG", "BOLD", "RESET",
            "CYAN", "GREEN", "YELLOW", "RED", "MAGENTA", "BLUE", "WHITE", "GRAY", "ORANGE"
        ]}

    if theme_name == "tokyo_night":
        return {
            "CYAN_BG": "\033[48;2;61;89;161;38;2;192;202;245m",
            "GREEN_BG": "\033[48;2;115;218;139;30m",
            "YELLOW_BG": "\033[48;2;224;175;104;30m",
            "MAGENTA_BG": "\033[48;2;187;154;247;30m",
            "RED_BG": "\033[48;2;247;118;142;30m",
            "BLUE_BG": "\033[48;2;122;162;247;30m",
            "BOLD": "\033[1m",
            "RESET": "\033[0m",
            "CYAN": "\033[38;2;125;207;255m",
            "GREEN": "\033[38;2;115;218;139m",
            "YELLOW": "\033[38;2;224;175;104m",
            "RED": "\033[38;2;247;118;142m",
            "MAGENTA": "\033[38;2;187;154;247m",
            "BLUE": "\033[38;2;122;162;247m",
            "WHITE": "\033[38;2;192;202;245m",
            "GRAY": "\033[38;2;86;95;137m",
            "ORANGE": "\033[38;2;255;158;100m"
        }
    elif theme_name == "catppuccin":
        return {
            "CYAN_BG": "\033[48;2;137;220;235;30m",
            "GREEN_BG": "\033[48;2;166;227;161;30m",
            "YELLOW_BG": "\033[48;2;249;226;175;30m",
            "MAGENTA_BG": "\033[48;2;203;166;247;30m",
            "RED_BG": "\033[48;2;243;139;168;30m",
            "BLUE_BG": "\033[48;2;137;180;250;30m",
            "BOLD": "\033[1m",
            "RESET": "\033[0m",
            "CYAN": "\033[38;2;148;226;213m",
            "GREEN": "\033[38;2;166;227;161m",
            "YELLOW": "\033[38;2;249;226;175m",
            "RED": "\033[38;2;243;139;168m",
            "MAGENTA": "\033[38;2;203;166;247m",
            "BLUE": "\033[38;2;137;180;250m",
            "WHITE": "\033[38;2;205;214;244m",
            "GRAY": "\033[38;2;108;112;134m",
            "ORANGE": "\033[38;2;250;179;135m"
        }
    elif theme_name == "nord":
        return {
            "CYAN_BG": "\033[48;2;136;192;208;30m",
            "GREEN_BG": "\033[48;2;163;190;140;30m",
            "YELLOW_BG": "\033[48;2;235;203;139;30m",
            "MAGENTA_BG": "\033[48;2;180;142;173;30m",
            "RED_BG": "\033[48;2;191;97;106;30m",
            "BLUE_BG": "\033[48;2;129;161;193;30m",
            "BOLD": "\033[1m",
            "RESET": "\033[0m",
            "CYAN": "\033[38;2;136;192;208m",
            "GREEN": "\033[38;2;163;190;140m",
            "YELLOW": "\033[38;2;235;203;139m",
            "RED": "\033[38;2;191;97;106m",
            "MAGENTA": "\033[38;2;180;142;173m",
            "BLUE": "\033[38;2;129;161;193m",
            "WHITE": "\033[38;2;236;239;244m",
            "GRAY": "\033[38;2;76;86;106m",
            "ORANGE": "\033[38;2;208;135;112m"
        }
    elif theme_name == "cyberpunk":
        return {
            "CYAN_BG": "\033[48;2;0;255;238;30m",
            "GREEN_BG": "\033[48;2;0;255;102;30m",
            "YELLOW_BG": "\033[48;2;255;238;0;30m",
            "MAGENTA_BG": "\033[48;2;255;0;127;30m",
            "RED_BG": "\033[48;2;255;51;51;30m",
            "BLUE_BG": "\033[48;2;0;153;255;30m",
            "BOLD": "\033[1m",
            "RESET": "\033[0m",
            "CYAN": "\033[38;2;0;255;238m",
            "GREEN": "\033[38;2;0;255;102m",
            "YELLOW": "\033[38;2;255;238;0m",
            "RED": "\033[38;2;255;51;51m",
            "MAGENTA": "\033[38;2;255;0;127m",
            "BLUE": "\033[38;2;0;153;255m",
            "WHITE": "\033[38;2;255;255;255m",
            "GRAY": "\033[38;2;90;90;110m",
            "ORANGE": "\033[38;2;255;136;0m"
        }
    elif theme_name == "plain":
        return {
            "CYAN_BG": "", "GREEN_BG": "", "YELLOW_BG": "", "MAGENTA_BG": "",
            "RED_BG": "", "BLUE_BG": "", "BOLD": "\033[1m", "RESET": "\033[0m",
            "CYAN": "\033[36m", "GREEN": "\033[32m", "YELLOW": "\033[33m",
            "RED": "\033[31m", "MAGENTA": "\033[35m", "BLUE": "\033[34m",
            "WHITE": "\033[37m", "GRAY": "\033[90m", "ORANGE": "\033[33m"
        }
    else:
        # Default ANSI theme (vibrant modern palette)
        return {
            "CYAN_BG": "\033[46;30m",
            "GREEN_BG": "\033[42;30m",
            "YELLOW_BG": "\033[43;30m",
            "MAGENTA_BG": "\033[45;30m",
            "RED_BG": "\033[41;97m",
            "BLUE_BG": "\033[44;97m",
            "BOLD": "\033[1m",
            "RESET": "\033[0m",
            "CYAN": "\033[96m",
            "GREEN": "\033[92m",
            "YELLOW": "\033[93m",
            "RED": "\033[91m",
            "MAGENTA": "\033[95m",
            "BLUE": "\033[94m",
            "WHITE": "\033[97m",
            "GRAY": "\033[90m",
            "ORANGE": "\033[33m"
        }

def make_bar(pct, length, colors, low_good=True, smooth=True):
    pct = min(max(pct, 0.0), 100.0)
    
    if smooth:
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
    else:
        filled = int(round(length * (pct / 100.0)))
        bar = "█" * filled + "░" * (length - filled)
    
    if low_good:
        color = colors["GREEN"] if pct < 50 else (colors["YELLOW"] if pct < 80 else colors["RED"])
    else:
        color = colors["GREEN"] if pct > 50 else (colors["YELLOW"] if pct > 20 else colors["RED"])

    return f"{color}{bar}{colors['RESET']}"

def calculate_cost(model_name, in_tokens, out_tokens, cached_tokens=0):
    m = model_name.lower()
    if "pro" in m:
        rate_in = 3.50 / 1_000_000
        rate_out = 14.00 / 1_000_000
        rate_cache = 0.875 / 1_000_000
    elif "claude" in m or "sonnet" in m:
        rate_in = 3.00 / 1_000_000
        rate_out = 15.00 / 1_000_000
        rate_cache = 0.75 / 1_000_000
    else:
        # Default Gemini Flash
        rate_in = 0.75 / 1_000_000
        rate_out = 3.75 / 1_000_000
        rate_cache = 0.1875 / 1_000_000

    normal_in = max(in_tokens - cached_tokens, 0)
    cost = (normal_in * rate_in) + (cached_tokens * rate_cache) + (out_tokens * rate_out)
    savings = cached_tokens * (rate_in - rate_cache) if cached_tokens > 0 else 0.0
    return cost, savings

def parse_quota(quota_dict, rate_limits_dict, keys):
    for k in keys:
        if k in quota_dict:
            q = quota_dict[k]
            if isinstance(q, dict):
                rem_fraction = q.get("remaining_fraction")
                reset_sec = q.get("reset_in_seconds", 0)
                reset_time = q.get("reset_time", "")
                if rem_fraction is not None:
                    rem_pct = rem_fraction * 100.0
                    used_pct = 100.0 - rem_pct
                    return (used_pct, rem_pct, reset_sec, reset_time)

    for k in keys:
        if k in rate_limits_dict:
            rl = rate_limits_dict[k]
            if isinstance(rl, dict):
                used_pct = rl.get("used_percentage", 0.0)
                reset_sec = rl.get("reset_in_seconds", 0)
                reset_time = rl.get("reset_time", "")
                rem_pct = 100.0 - used_pct
                return (used_pct, rem_pct, reset_sec, reset_time)

    return None

def get_active_profile_name():
    env_p = os.environ.get("AGY_PROFILE") or os.environ.get("ANTIGRAVITY_PROFILE")
    if env_p:
        return env_p
    active_file = os.path.join(CUSTOM_DIR, "active_profile.json")
    if os.path.exists(active_file):
        try:
            with open(active_file, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d.get("active", "perfil1")
        except Exception:
            pass
    gem_home = os.environ.get("GEMINI_HOME") or os.environ.get("PERFIL_ROOT")
    if gem_home:
        base = os.path.basename(gem_home)
        if base and base != "ma038":
            return base
    return "perfil1"

def save_profile_quota(profile_name, email, quota_5h, quota_weekly):
    if not quota_5h and not quota_weekly:
        return
    cache_file = os.path.join(CUSTOM_DIR, "profiles_quotas.json")
    quotas = {}
    if os.path.exists(cache_file):
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                quotas = json.load(f)
        except Exception:
            quotas = {}
    entry = quotas.get(profile_name, {})
    if email:
        entry["email"] = email
    entry["updated_at"] = datetime.datetime.now().isoformat()
    if quota_5h:
        entry["quota_5h"] = {
            "used_pct": quota_5h[0],
            "rem_pct": quota_5h[1],
            "reset_in_seconds": quota_5h[2],
            "reset_time": quota_5h[3]
        }
    if quota_weekly:
        entry["quota_weekly"] = {
            "used_pct": quota_weekly[0],
            "rem_pct": quota_weekly[1],
            "reset_in_seconds": quota_weekly[2],
            "reset_time": quota_weekly[3]
        }
    quotas[profile_name] = entry
    try:
        os.makedirs(CUSTOM_DIR, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump(quotas, f, indent=2)
    except Exception:
        pass

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.stdout.write("✦ Antigravity CLI")
            return

        data = json.loads(raw_input)
        conf = load_config()
        colors = get_theme_colors(conf.get("theme", "default"))
        nerd = conf.get("nerd_fonts", False)
        smooth = conf.get("smooth_bars", True)

        # Terminal width resolution
        term_width = data.get("terminal_width")
        if not term_width or term_width <= 0:
            try:
                term_width = os.get_terminal_size().columns
            except Exception:
                term_width = 140

        is_wide = term_width >= 140
        is_medium = 100 <= term_width < 140
        is_narrow = term_width < 100

        # Session & Identifiers
        session_id = data.get("session_id") or data.get("conversation_id", "")
        short_id = session_id[:8] if session_id else "new"
        title = data.get("title", "")
        email = data.get("email", "")
        plan_tier = data.get("plan_tier", "")
        version = data.get("version", "")

        state = str(data.get("agent_state", "idle")).upper()
        start_time, elapsed_time, elapsed_sec = get_session_info(session_id, conf.get("max_cached_sessions", 50))

        # Model & Effort
        model_info = data.get("model") or {}
        model_name = model_info.get("display_name", "Gemini")
        effort = model_info.get("effort")
        effort_str = f"⚡{effort}" if effort else ""

        cycle_mode = data.get("cycle_mode", "")
        mode_str = f"[{cycle_mode}]" if cycle_mode else ""

        # Context Window & Tokens
        cw = data.get("context_window") or {}
        used_pct = cw.get("used_percentage", 0.0) or 0.0
        in_tokens = cw.get("total_input_tokens", 0)
        out_tokens = cw.get("total_output_tokens", 0)
        cached_tokens = cw.get("cached_tokens", 0)
        total_tokens = in_tokens + out_tokens
        cw_size = cw.get("context_window_size", 1_048_576)
        exceeds_200k = data.get("exceeds_200k_tokens", False)

        # Tokens/s Speed Calculation
        tps_str = ""
        if conf.get("show_tokens_per_sec") and elapsed_sec > 5 and total_tokens > 0:
            tps = total_tokens / elapsed_sec
            tps_str = f"{tps:.1f}t/s"

        # Commercial API Cost & Cache Savings
        estimated_cost, cache_savings = calculate_cost(model_name, in_tokens, out_tokens, cached_tokens)
        cost_str = f"${estimated_cost:.4f}" if estimated_cost < 1.0 else f"${estimated_cost:.2f}"
        savings_str = f"${cache_savings:.4f}" if cache_savings < 1.0 else f"${cache_savings:.2f}"

        # Quotas (5h and Weekly)
        quota = data.get("quota") or {}
        rate_limits = data.get("rate_limits") or {}
        quota_5h = parse_quota(quota, rate_limits, ["gemini-5h", "3p-5h", "5h", "five_hour"])
        quota_weekly = parse_quota(quota, rate_limits, ["gemini-weekly", "3p-weekly", "weekly", "seven_day", "7d"])

        # Subagents & Tasks
        subagents = data.get("subagents") or []
        running_subagents = [s.get("name") or s.get("role", "subagent") for s in subagents if s.get("status") == "running"]
        active_agent = (data.get("agent") or {}).get("name", "")

        task_count = data.get("task_count", 0)
        artifact_count = data.get("artifact_count", 0)
        sandbox = (data.get("sandbox") or {}).get("enabled", False)

        # Workspace & VCS
        vcs = data.get("vcs") or {}
        vcs_type = vcs.get("type", "git")
        branch = vcs.get("branch", "")
        dirty = vcs.get("dirty", False)
        ahead = vcs.get("ahead", 0) or vcs.get("commits_ahead", 0)
        behind = vcs.get("behind", 0) or vcs.get("commits_behind", 0)

        workspace = data.get("workspace") or {}
        cur_dir = workspace.get("current_dir") or data.get("cwd", "")
        dir_name = os.path.basename(cur_dir) if cur_dir else ""
        if not branch and cur_dir:
            branch = get_git_branch_fast(cur_dir)

        # MCP & Tooling ecosystem
        mcp_data = data.get("mcp") or data.get("mcp_servers") or []
        mcp_count = data.get("mcp_count") or (len(mcp_data) if isinstance(mcp_data, (list, dict)) else 0)
        skills_data = data.get("skills") or []
        skills_count = data.get("skills_count") or (len(skills_data) if isinstance(skills_data, (list, dict)) else 0)

        # System Health (RAM, Host OS)
        ram_pct, ram_total = get_system_ram()
        host_os = platform.system()
        if host_os == "Darwin":
            host_os = "macOS"

        RESET = colors["RESET"]
        BOLD = colors["BOLD"]

        # Icons (Nerd Font vs standard Unicode)
        ico_agent = "󰚩 " if nerd else "🤖 "
        ico_model = "󱚣 " if nerd else "✦ "
        ico_speed = "󰓅 " if nerd else "⚡"
        ico_clock = "󱑂 " if nerd else "🕒 "
        ico_stopwatch = "󱑂 " if nerd else "⏱ "
        ico_ram = "󰍛 " if nerd else "🧠 "
        ico_mcp = "󰒋 " if nerd else "🔌 "
        ico_skills = "󰒓 " if nerd else "⚡"
        ico_folder = "󰉋 " if nerd else "📁 "
        ico_branch = " " if nerd else "git:"
        ico_tasks = "󰒓 " if nerd else "⚙️ "
        ico_docs = "󰈙 " if nerd else "📄 "
        ico_sandbox = "󰒃 " if nerd else "🛡️ "
        ico_user = " " if nerd else "👤 "
        ico_host = "󰖳 " if (nerd and host_os == "Windows") else ("󰌽 " if (nerd and host_os == "Linux") else ("󰀵 " if (nerd and host_os == "macOS") else "🖥️ "))

        # State Pill Badge
        if conf.get("theme") == "plain":
            state_badge = f"[{state}]"
        else:
            if state == "IDLE":
                state_badge = f"{colors['GREEN_BG']} IDLE {RESET}"
            elif "THINK" in state:
                state_badge = f"{colors['YELLOW_BG']} THINKING {RESET}"
            elif "TOOL" in state or "EXEC" in state:
                state_badge = f"{colors['YELLOW_BG']} TOOL USE {RESET}"
            elif "REVIEW" in state:
                state_badge = f"{colors['CYAN_BG']} REVIEWING {RESET}"
            elif "ERROR" in state:
                state_badge = f"{colors['RED_BG']} ERROR {RESET}"
            else:
                state_badge = f"{colors['BLUE_BG']} {state} {RESET}"

        # =========================================================================
        # LINE 1: SESSION, MODEL, REASONING RUNTIME & API BILLING
        # =========================================================================
        line1_items = [state_badge]

        # Chat ID & Title
        if not is_narrow:
            chat_code_block = f"{colors['MAGENTA_BG']} #{short_id} {RESET}" if conf.get("theme") != "plain" else f"#{short_id}"
            if title and is_wide:
                chat_code_block += f" {colors['WHITE']}\"{title[:18]}\"{RESET}"
            line1_items.append(chat_code_block)

        # Model & Effort
        model_block = f"{BOLD}{colors['CYAN']}{ico_model}{model_name}{RESET}"
        if effort_str:
            model_block += f" {colors['YELLOW']}{effort_str}{RESET}"
        if mode_str and not is_narrow:
            model_block += f" {colors['MAGENTA']}{mode_str}{RESET}"
        line1_items.append(model_block)

        # Context Window Saturation Bar (24 blocks on wide screens)
        bar_len_l1 = 24 if is_wide else (12 if is_medium else 8)
        token_bar = make_bar(used_pct, length=bar_len_l1, colors=colors, low_good=True, smooth=smooth)
        ctx_color = colors["GREEN"] if used_pct < 50 else (colors["YELLOW"] if used_pct < 80 else colors["RED"])

        if is_wide:
            cache_info = f" {colors['CYAN']}⚡cache:{format_tokens(cached_tokens)}{RESET}" if cached_tokens > 0 else ""
            warn_200k = f" {colors['RED']}[>200k]{RESET}" if exceeds_200k else ""
            tokens_block = (
                f"{BOLD}{colors['WHITE']}Tokens:{RESET} [{token_bar}] {ctx_color}{used_pct:.1f}%{RESET} "
                f"{colors['GRAY']}(In:{RESET}{colors['CYAN']}{format_tokens(in_tokens)}{RESET} "
                f"{colors['GRAY']}Out:{RESET}{colors['YELLOW']}{format_tokens(out_tokens)}{RESET}{cache_info} "
                f"{colors['GRAY']}Total:{RESET}{colors['WHITE']}{format_tokens(total_tokens)}{RESET}{colors['GRAY']}/{format_tokens(cw_size)}){RESET}{warn_200k}"
            )
        else:
            tokens_block = f"Tokens: [{token_bar}] {ctx_color}{used_pct:.1f}%{RESET} ({format_tokens(total_tokens)})"
        line1_items.append(tokens_block)

        # Commercial API Cost & Savings
        if conf.get("show_cost", True) and not is_narrow:
            cost_block = f"{BOLD}{colors['GREEN']}Cost: {cost_str}{RESET}"
            if cache_savings > 0.0001 and is_wide:
                cost_block += f" {colors['CYAN']}(Saved {savings_str}){RESET}"
            line1_items.append(cost_block)

        # Generation Speed (t/s)
        if tps_str and is_wide:
            line1_items.append(f"{colors['CYAN']}{ico_speed}{tps_str}{RESET}")

        # Elapsed Duration
        if not is_narrow:
            time_block = f"{colors['GRAY']}{ico_stopwatch}{elapsed_time}{RESET}"
            if is_wide:
                time_block += f" {colors['GRAY']}(Start:{colors['WHITE']}{start_time}{colors['GRAY']}){RESET}"
            line1_items.append(time_block)

        # =========================================================================
        # LINE 2: QUOTA POOLS, RATE LIMITS, IDENTITY & AUTONOMOUS AGENTS CLUSTER
        # =========================================================================
        line2_items = []
        quota_bar_len = 20 if is_wide else (10 if is_medium else 6)

        # Quota 5h (Rolling Limit)
        if conf.get("show_quota_5h", True):
            if quota_5h:
                used_h, rem_h, reset_h, _ = quota_5h
                bar_5h = make_bar(used_h, length=quota_bar_len, colors=colors, low_good=True, smooth=smooth)
                h_color = colors["GREEN"] if used_h < 70 else (colors["YELLOW"] if used_h < 90 else colors["RED"])
                reset_txt = f" {colors['GRAY']}(reset {format_seconds(reset_h)}){RESET}" if reset_h > 0 else ""
                pace_warn = f" {colors['RED']}[HIGH PACE]{RESET}" if used_h > 75 and reset_h > 7200 else ""
                line2_items.append(f"{BOLD}5h:{RESET} [{bar_5h}] {h_color}{used_h:.0f}%{RESET}{reset_txt}{pace_warn}")
            else:
                bar_empty = make_bar(0.0, length=quota_bar_len, colors=colors, low_good=True, smooth=smooth)
                line2_items.append(f"{BOLD}5h:{RESET} [{bar_empty}] {colors['GREEN']}0%{RESET}")

        # Quota Weekly (7-Day Limit)
        if conf.get("show_quota_weekly", True) and not is_narrow:
            if quota_weekly:
                used_w, rem_w, reset_w, _ = quota_weekly
                bar_w = make_bar(used_w, length=quota_bar_len, colors=colors, low_good=True, smooth=smooth)
                w_color = colors["GREEN"] if used_w < 70 else (colors["YELLOW"] if used_w < 90 else colors["RED"])
                reset_w_txt = f" {colors['GRAY']}({format_seconds(reset_w)}){RESET}" if reset_w > 0 and is_wide else ""
                line2_items.append(f"{BOLD}7d:{RESET} [{bar_w}] {w_color}{used_w:.0f}%{RESET}{reset_w_txt}")
            else:
                bar_empty_w = make_bar(0.0, length=quota_bar_len, colors=colors, low_good=True, smooth=smooth)
                line2_items.append(f"{BOLD}7d:{RESET} [{bar_empty_w}] {colors['GREEN']}0%{RESET}")

        # Quota Velocity / Pace Indicator
        if conf.get("show_burn_rate", True) and quota_5h and is_wide:
            used_h, _, reset_h, _ = quota_5h
            if reset_h > 0 and reset_h < 18000:
                elapsed_window = max(18000 - reset_h, 300)
                burn_per_hr = (used_h / elapsed_window) * 3600
                if burn_per_hr > 25.0:
                    burn_tag = f"{colors['RED']}🔥 Burn:{burn_per_hr:.1f}%/h{RESET}"
                else:
                    burn_tag = f"{colors['GREEN']}🟢 Safe Pace{RESET}"
                line2_items.append(burn_tag)

        # Active Profile & Quota Cache Sync
        active_prof = get_active_profile_name()
        save_profile_quota(active_prof, email, quota_5h, quota_weekly)

        # Account / Email, Profile & Plan Tier
        if conf.get("show_email", True) and email and not is_narrow:
            plan_str = f" {colors['YELLOW']}[{plan_tier}]{RESET}" if plan_tier else ""
            prof_str = f" {colors['MAGENTA']}({active_prof}){RESET}" if conf.get("show_profile", True) and is_wide else ""
            line2_items.append(f"{colors['CYAN']}{ico_user}{email}{RESET}{prof_str}{plan_str}")
        elif plan_tier and not is_narrow:
            prof_str = f" {colors['MAGENTA']}({active_prof}){RESET}" if conf.get("show_profile", True) and is_wide else ""
            line2_items.append(f"{colors['GRAY']}Plan:{colors['YELLOW']}[{plan_tier}]{RESET}{prof_str}")
        elif conf.get("show_profile", True) and not is_narrow:
            line2_items.append(f"{colors['MAGENTA']}{ico_user}{active_prof}{RESET}")

        # Subagent Swarm Cluster
        if conf.get("show_subagents", True) and running_subagents:
            sub_names = f": {','.join(running_subagents)}" if is_wide else ""
            badge_sub = f"{colors['YELLOW_BG']} {ico_agent}Subagents ({len(running_subagents)}){sub_names} {RESET}" if conf.get("theme") != "plain" else f"Subagents:{len(running_subagents)}"
            line2_items.append(badge_sub)
        elif active_agent and not is_narrow:
            line2_items.append(f"{colors['BLUE']}{ico_agent}{active_agent}{RESET}")

        # Async Background Tasks
        if conf.get("show_tasks", True) and task_count:
            line2_items.append(f"{colors['BLUE']}{ico_tasks}Tasks:{task_count}{RESET}")

        # Artifacts & Documentation
        if conf.get("show_artifacts", True) and artifact_count and not is_narrow:
            line2_items.append(f"{colors['CYAN']}{ico_docs}Docs:{artifact_count}{RESET}")

        # =========================================================================
        # LINE 3: ENVIRONMENT, SYSTEM HEALTH, WORKSPACE, GIT & TOOLING ENGINE
        # =========================================================================
        line3_items = []

        # System RAM Utilization (Cross-platform pure Python)
        if conf.get("show_ram", True) and ram_pct is not None:
            ram_col = colors['GREEN'] if ram_pct < 70 else (colors['YELLOW'] if ram_pct < 85 else colors['RED'])
            total_str = f"/{ram_total}" if ram_total and not is_narrow else ""
            if is_wide:
                ram_bar = make_bar(ram_pct, length=8, colors=colors, low_good=True, smooth=smooth)
                line3_items.append(f"{ico_ram}{BOLD}RAM:{RESET} [{ram_bar}] {ram_col}{ram_pct}%{total_str}{RESET}")
            else:
                line3_items.append(f"{ico_ram}{ram_col}RAM:{ram_pct}%{total_str}{RESET}")

        # Host Operating System
        if host_os and is_wide:
            line3_items.append(f"{colors['WHITE']}{ico_host}{host_os}{RESET}")

        # Workspace Directory
        if conf.get("show_workspace", True) and dir_name:
            line3_items.append(f"{colors['WHITE']}{ico_folder}{dir_name}{RESET}")

        # VCS & Git Intelligence
        if conf.get("show_git", True) and branch:
            dirty_flag = f"{colors['RED']}*{RESET}" if dirty else ""
            diff_str = ""
            if (ahead or behind) and is_wide:
                diff_str = f" {colors['GREEN']}+{ahead}{RESET}{colors['RED']}-{behind}{RESET}"
            line3_items.append(f"{colors['MAGENTA']}{ico_branch}{branch}{dirty_flag}{diff_str}{RESET}")

        # MCP Servers & Tools Ecosystem
        if conf.get("show_mcp", True) and mcp_count and not is_narrow:
            line3_items.append(f"{colors['CYAN']}{ico_mcp}MCP:{mcp_count} active{RESET}")

        # Skills Engine
        if conf.get("show_skills", True) and skills_count and is_wide:
            line3_items.append(f"{colors['YELLOW']}{ico_skills}Skills:{skills_count}{RESET}")

        # Security Sandbox Status
        if conf.get("show_sandbox", True) and not is_narrow:
            if sandbox:
                line3_items.append(f"{colors['GREEN']}{ico_sandbox}Sandbox:ON{RESET}")
            elif is_wide:
                line3_items.append(f"{colors['GRAY']}{ico_sandbox}Sandbox:OFF{RESET}")

        # Real-time Local Clock
        if conf.get("show_clock", True):
            now_clock = datetime.datetime.now().strftime("%H:%M:%S" if not is_narrow else "%H:%M")
            line3_items.append(f"{colors['GRAY']}{ico_clock}{colors['WHITE']}{now_clock}{RESET}")

        # Engine & Runtime Version
        if conf.get("show_version", True):
            py_ver = f"Py{sys.version_info.major}.{sys.version_info.minor}"
            if version and is_wide:
                line3_items.append(f"{colors['GRAY']}agy v{version} • {py_ver}{RESET}")
            elif version:
                line3_items.append(f"{colors['GRAY']}v{version}{RESET}")
            elif is_wide:
                line3_items.append(f"{colors['GRAY']}{py_ver}{RESET}")

        # Delimiter
        sep = f" {colors['GRAY']}│{RESET} "
        lines = [sep.join(line1_items), sep.join(line2_items)]
        if conf.get("show_line3", True) and line3_items:
            lines.append(sep.join(line3_items))

        output = "\n".join(lines)
        sys.stdout.write(output)

    except Exception as e:
        debug_log(f"Unhandled error: {e}")
        sys.stdout.write("✦ Antigravity CLI")

if __name__ == "__main__":
    main()

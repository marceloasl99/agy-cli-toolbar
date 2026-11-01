import sys
import json
import datetime
import os

# Ensure full UTF-8 support on Windows console
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

CUSTOM_DIR = os.path.join(os.path.expanduser("~"), ".antigravity-custom")
SESSION_FILE = os.path.join(CUSTOM_DIR, ".session_time.json")
CONFIG_FILE = os.path.join(CUSTOM_DIR, "config.json")
LOG_FILE = os.path.join(CUSTOM_DIR, "statusline.log")

DEFAULT_CONFIG = {
    "show_cost": True,
    "show_tokens_per_sec": True,
    "show_quota_5h": True,
    "show_quota_weekly": True,
    "show_subagents": True,
    "show_tasks": True,
    "show_artifacts": True,
    "show_git": True,
    "show_workspace": True,
    "show_email": True,
    "theme": "default",       # "default", "tokyo_night", "catppuccin", "plain"
    "nerd_fonts": False,      # Enable for Nerd Font icons
    "max_cached_sessions": 50
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                user_conf = json.load(f)
                conf = DEFAULT_CONFIG.copy()
                conf.update(user_conf)
                return conf
        except Exception:
            pass
    return DEFAULT_CONFIG.copy()

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

def get_theme_colors(theme_name):
    if os.environ.get("NO_COLOR"):
        return {k: "" for k in [
            "CYAN_BG", "GREEN_BG", "YELLOW_BG", "MAGENTA_BG", "BOLD", "RESET",
            "CYAN", "GREEN", "YELLOW", "RED", "MAGENTA", "BLUE", "WHITE", "GRAY"
        ]}

    if theme_name == "tokyo_night":
        return {
            "CYAN_BG": "\033[48;2;61;89;161;38;2;192;202;245m",
            "GREEN_BG": "\033[48;2;115;218;139;30m",
            "YELLOW_BG": "\033[48;2;224;175;104;30m",
            "MAGENTA_BG": "\033[48;2;187;154;247;30m",
            "BOLD": "\033[1m",
            "RESET": "\033[0m",
            "CYAN": "\033[38;2;125;207;255m",
            "GREEN": "\033[38;2;115;218;139m",
            "YELLOW": "\033[38;2;224;175;104m",
            "RED": "\033[38;2;247;118;142m",
            "MAGENTA": "\033[38;2;187;154;247m",
            "BLUE": "\033[38;2;122;162;247m",
            "WHITE": "\033[38;2;192;202;245m",
            "GRAY": "\033[38;2;86;95;137m"
        }
    elif theme_name == "catppuccin":
        return {
            "CYAN_BG": "\033[48;2;137;220;235;30m",
            "GREEN_BG": "\033[48;2;166;227;161;30m",
            "YELLOW_BG": "\033[48;2;249;226;175;30m",
            "MAGENTA_BG": "\033[48;2;203;166;247;30m",
            "BOLD": "\033[1m",
            "RESET": "\033[0m",
            "CYAN": "\033[38;2;148;226;213m",
            "GREEN": "\033[38;2;166;227;161m",
            "YELLOW": "\033[38;2;249;226;175m",
            "RED": "\033[38;2;243;139;168m",
            "MAGENTA": "\033[38;2;203;166;247m",
            "BLUE": "\033[38;2;137;180;250m",
            "WHITE": "\033[38;2;205;214;244m",
            "GRAY": "\033[38;2;108;112;134m"
        }
    elif theme_name == "plain":
        return {
            "CYAN_BG": "", "GREEN_BG": "", "YELLOW_BG": "", "MAGENTA_BG": "",
            "BOLD": "\033[1m", "RESET": "\033[0m",
            "CYAN": "\033[36m", "GREEN": "\033[32m", "YELLOW": "\033[33m",
            "RED": "\033[31m", "MAGENTA": "\033[35m", "BLUE": "\033[34m",
            "WHITE": "\033[37m", "GRAY": "\033[90m"
        }
    else:
        # Default ANSI theme
        return {
            "CYAN_BG": "\033[46;30m",
            "GREEN_BG": "\033[42;30m",
            "YELLOW_BG": "\033[43;30m",
            "MAGENTA_BG": "\033[45;30m",
            "BOLD": "\033[1m",
            "RESET": "\033[0m",
            "CYAN": "\033[96m",
            "GREEN": "\033[92m",
            "YELLOW": "\033[93m",
            "RED": "\033[91m",
            "MAGENTA": "\033[95m",
            "BLUE": "\033[94m",
            "WHITE": "\033[97m",
            "GRAY": "\033[90m"
        }

def make_bar(pct, length, colors, low_good=True):
    pct = min(max(pct, 0.0), 100.0)
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
    return cost

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

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.stdout.write("Antigravity CLI")
            return

        data = json.loads(raw_input)
        conf = load_config()
        colors = get_theme_colors(conf.get("theme", "default"))

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

        # Commercial API Cost
        estimated_cost = calculate_cost(model_name, in_tokens, out_tokens, cached_tokens)
        cost_str = f"${estimated_cost:.4f}" if estimated_cost < 1.0 else f"${estimated_cost:.2f}"

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

        workspace = data.get("workspace") or {}
        cur_dir = workspace.get("current_dir") or data.get("cwd", "")
        dir_name = os.path.basename(cur_dir) if cur_dir else ""

        RESET = colors["RESET"]
        BOLD = colors["BOLD"]

        # Badge de Estado
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
            else:
                state_badge = f"{colors['YELLOW_BG']} {state} {RESET}"

        # ------------------- LINE 1 -------------------
        line1_items = [state_badge]

        # Chat ID & Title
        if not is_narrow:
            chat_code_block = f"{colors['MAGENTA_BG']} #{short_id} {RESET}" if conf.get("theme") != "plain" else f"#{short_id}"
            if title and is_wide:
                chat_code_block += f" {colors['WHITE']}\"{title[:18]}\"{RESET}"
            line1_items.append(chat_code_block)

        # Model Info
        model_block = f"{BOLD}{colors['CYAN']}{model_name}{RESET}"
        if effort_str:
            model_block += f" {colors['YELLOW']}{effort_str}{RESET}"
        if mode_str and not is_narrow:
            model_block += f" {colors['MAGENTA']}{mode_str}{RESET}"
        line1_items.append(model_block)

        # Token Bargraph (Top Line: 24 blocks on wide screens)
        bar_len_l1 = 24 if is_wide else (12 if is_medium else 8)
        token_bar = make_bar(used_pct, length=bar_len_l1, colors=colors, low_good=True)
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

        # API Cost
        if conf.get("show_cost", True) and not is_narrow:
            line1_items.append(f"{BOLD}{colors['GREEN']}Cost: {cost_str}{RESET}")

        # Generation Speed (t/s)
        if tps_str and is_wide:
            line1_items.append(f"{colors['CYAN']}⚡{tps_str}{RESET}")

        # Start time and elapsed
        if not is_narrow:
            time_block = f"{colors['GRAY']}Start:{colors['WHITE']}{start_time}{RESET} {colors['GRAY']}(+{elapsed_time}){RESET}"
            line1_items.append(time_block)

        # ------------------- LINE 2 (DUPLICATED BARGRAPH SIZE: 20 BLOCKS EACH) -------------------
        line2_items = []
        # Double the bargraph size from 10 to 20 blocks on wide monitors
        quota_bar_len = 20 if is_wide else (10 if is_medium else 6)

        # Quota 5h (20 blocks wide)
        if conf.get("show_quota_5h", True):
            if quota_5h:
                used_h, rem_h, reset_h, _ = quota_5h
                bar_5h = make_bar(used_h, length=quota_bar_len, colors=colors, low_good=True)
                h_color = colors["GREEN"] if used_h < 70 else (colors["YELLOW"] if used_h < 90 else colors["RED"])
                reset_txt = f" {colors['GRAY']}({format_seconds(reset_h)}){RESET}" if reset_h > 0 else ""
                pace_warn = f" {colors['RED']}[HIGH PACE]{RESET}" if used_h > 75 and reset_h > 7200 else ""
                line2_items.append(f"{BOLD}5h:{RESET} [{bar_5h}] {h_color}{used_h:.0f}%{RESET}{reset_txt}{pace_warn}")
            else:
                bar_empty = make_bar(0.0, length=quota_bar_len, colors=colors, low_good=True)
                line2_items.append(f"{BOLD}5h:{RESET} [{bar_empty}] {colors['GREEN']}0%{RESET}")

        # Quota Weekly (20 blocks wide)
        if conf.get("show_quota_weekly", True) and not is_narrow:
            if quota_weekly:
                used_w, rem_w, reset_w, _ = quota_weekly
                bar_w = make_bar(used_w, length=quota_bar_len, colors=colors, low_good=True)
                w_color = colors["GREEN"] if used_w < 70 else (colors["YELLOW"] if used_w < 90 else colors["RED"])
                reset_w_txt = f" {colors['GRAY']}({format_seconds(reset_w)}){RESET}" if reset_w > 0 and is_wide else ""
                line2_items.append(f"{BOLD}7d:{RESET} [{bar_w}] {w_color}{used_w:.0f}%{RESET}{reset_w_txt}")
            else:
                bar_empty_w = make_bar(0.0, length=quota_bar_len, colors=colors, low_good=True)
                line2_items.append(f"{BOLD}7d:{RESET} [{bar_empty_w}] {colors['GREEN']}0%{RESET}")

        # Account / Email & Plan
        if conf.get("show_email", True) and email and not is_narrow:
            plan_str = f" ({plan_tier})" if plan_tier else ""
            line2_items.append(f"{colors['CYAN']}👤 {email}{plan_str}{RESET}")
        elif plan_tier and not is_narrow:
            line2_items.append(f"{colors['GRAY']}Plan:{colors['WHITE']}{plan_tier}{RESET}")

        # Subagents
        if conf.get("show_subagents", True) and running_subagents:
            badge_sub = f"{colors['YELLOW_BG']} Subagents ({len(running_subagents)}): {','.join(running_subagents)} {RESET}" if conf.get("theme") != "plain" else f"Subagents:{len(running_subagents)}"
            line2_items.append(badge_sub)
        elif active_agent:
            line2_items.append(f"{colors['BLUE']}Agent:{active_agent}{RESET}")

        # Tasks
        if conf.get("show_tasks", True) and task_count:
            line2_items.append(f"{colors['BLUE']}⚙️ Tasks:{task_count}{RESET}")

        # Artifacts
        if conf.get("show_artifacts", True) and artifact_count and not is_narrow:
            line2_items.append(f"{colors['CYAN']}📄 Docs:{artifact_count}{RESET}")

        # Sandbox
        if sandbox and not is_narrow:
            line2_items.append(f"{colors['MAGENTA']}[Sandbox]{RESET}")

        # Workspace Directory
        if conf.get("show_workspace", True) and dir_name and is_wide:
            line2_items.append(f"{colors['WHITE']}📁 {dir_name}{RESET}")

        # VCS / Git
        if conf.get("show_git", True) and branch:
            dirty_flag = f"{colors['RED']}*{RESET}" if dirty else ""
            vcs_tag = vcs_type if vcs_type != "git" else "git"
            line2_items.append(f"{colors['MAGENTA']}{vcs_tag}:{branch}{dirty_flag}{RESET}")

        # CLI Version
        if version and is_wide:
            line2_items.append(f"{colors['GRAY']}v{version}{RESET}")

        # Delimiter
        sep = f" {colors['GRAY']}│{RESET} "
        output = f"{sep.join(line1_items)}\n{sep.join(line2_items)}"
        sys.stdout.write(output)

    except Exception as e:
        debug_log(f"Unhandled error: {e}")
        sys.stdout.write("✦ Antigravity CLI")

if __name__ == "__main__":
    main()

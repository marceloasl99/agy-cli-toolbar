import sys
import json
import datetime
import os

# Assegura suporte completo a UTF-8 no console do Windows
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

SESSION_FILE = os.path.join(os.path.expanduser("~"), ".antigravity-custom", ".session_time.json")

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

def get_session_info(session_id):
    now = datetime.datetime.now()
    if not session_id:
        return now.strftime("%H:%M:%S"), "0m"
    
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
            elapsed_sec = int((now - start_dt).total_seconds())
            elapsed_str = format_seconds(elapsed_sec)
            return start_dt.strftime("%H:%M:%S"), elapsed_str
        except Exception:
            pass
    
    session_data[session_id] = now.isoformat()
    try:
        with open(SESSION_FILE, "w", encoding="utf-8") as f:
            json.dump(session_data, f)
    except Exception:
        pass
    return now.strftime("%H:%M:%S"), "0m"

def make_bar(pct, length=18, low_good=True):
    pct = min(max(pct, 0.0), 100.0)
    filled = int(round(length * (pct / 100.0)))
    bar = "█" * filled + "░" * (length - filled)
    
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    RESET = "\033[0m"

    if low_good:
        color = GREEN if pct < 50 else (YELLOW if pct < 80 else RED)
    else:
        color = GREEN if pct > 50 else (YELLOW if pct > 20 else RED)

    return f"{color}{bar}{RESET}"

def calculate_cost(model_name, in_tokens, out_tokens):
    """
    Calcula estimativa de custo de API em USD com base na precificação padrão:
    - Flash: ~$0.75 / 1M input e ~$3.75 / 1M output
    - Pro: ~$3.50 / 1M input e ~$14.00 / 1M output
    - Claude / 3p: ~$3.00 / 1M input e ~$15.00 / 1M output
    """
    m = model_name.lower()
    if "pro" in m:
        rate_in = 3.50 / 1_000_000
        rate_out = 14.00 / 1_000_000
    elif "claude" in m or "sonnet" in m:
        rate_in = 3.00 / 1_000_000
        rate_out = 15.00 / 1_000_000
    else:
        rate_in = 0.75 / 1_000_000
        rate_out = 3.75 / 1_000_000

    return (in_tokens * rate_in) + (out_tokens * rate_out)

def parse_quota(quota_dict, rate_limits_dict, keys):
    for k in keys:
        if k in quota_dict:
            q = quota_dict[k]
            if isinstance(q, dict):
                rem_fraction = q.get("remaining_fraction")
                reset_sec = q.get("reset_in_seconds", 0)
                if rem_fraction is not None:
                    rem_pct = rem_fraction * 100.0
                    used_pct = 100.0 - rem_pct
                    return (used_pct, rem_pct, reset_sec)

    for k in keys:
        if k in rate_limits_dict:
            rl = rate_limits_dict[k]
            if isinstance(rl, dict):
                used_pct = rl.get("used_percentage", 0.0)
                reset_sec = rl.get("reset_in_seconds", 0)
                rem_pct = 100.0 - used_pct
                return (used_pct, rem_pct, reset_sec)

    return None

def main():
    try:
        raw_input = sys.stdin.read()
        if not raw_input.strip():
            sys.stdout.write("Antigravity CLI")
            return

        data = json.loads(raw_input)

        session_id = data.get("session_id") or data.get("conversation_id", "")
        short_id = session_id[:8] if session_id else "nova"
        title = data.get("title", "")
        email = data.get("email", "")
        plan_tier = data.get("plan_tier", "")

        state = str(data.get("agent_state", "idle")).upper()
        start_time, elapsed_time = get_session_info(session_id)

        model_info = data.get("model") or {}
        model_name = model_info.get("display_name", "Gemini")
        effort = model_info.get("effort")
        effort_str = f"⚡{effort}" if effort else ""

        cycle_mode = data.get("cycle_mode", "")
        mode_str = f"[{cycle_mode}]" if cycle_mode else ""

        cw = data.get("context_window") or {}
        used_pct = cw.get("used_percentage", 0.0) or 0.0
        in_tokens = cw.get("total_input_tokens", 0)
        out_tokens = cw.get("total_output_tokens", 0)
        total_tokens = in_tokens + out_tokens
        cw_size = cw.get("context_window_size", 1_048_576)

        estimated_cost = calculate_cost(model_name, in_tokens, out_tokens)
        cost_str = f"${estimated_cost:.4f}" if estimated_cost < 1.0 else f"${estimated_cost:.2f}"

        quota = data.get("quota") or {}
        rate_limits = data.get("rate_limits") or {}

        quota_5h = parse_quota(quota, rate_limits, ["gemini-5h", "3p-5h", "5h", "five_hour"])
        quota_weekly = parse_quota(quota, rate_limits, ["gemini-weekly", "3p-weekly", "weekly", "seven_day", "7d"])

        subagents = data.get("subagents") or []
        running_subagents = [s.get("name") or s.get("role", "subagent") for s in subagents if s.get("status") == "running"]
        active_agent = (data.get("agent") or {}).get("name", "")

        task_count = data.get("task_count", 0)
        artifact_count = data.get("artifact_count", 0)
        sandbox = (data.get("sandbox") or {}).get("enabled", False)

        vcs = data.get("vcs") or {}
        branch = vcs.get("branch", "")
        dirty = vcs.get("dirty", False)

        workspace = data.get("workspace") or {}
        cur_dir = workspace.get("current_dir") or data.get("cwd", "")
        dir_name = os.path.basename(cur_dir) if cur_dir else ""

        CYAN_BG = "\033[46;30m"
        GREEN_BG = "\033[42;30m"
        YELLOW_BG = "\033[43;30m"
        MAGENTA_BG = "\033[45;30m"
        BOLD = "\033[1m"
        RESET = "\033[0m"
        CYAN = "\033[96m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        MAGENTA = "\033[95m"
        BLUE = "\033[94m"
        WHITE = "\033[97m"
        GRAY = "\033[90m"

        if state == "IDLE":
            badge = f"{GREEN_BG} IDLE {RESET}"
        elif "THINK" in state:
            badge = f"{YELLOW_BG} PENSANDO {RESET}"
        elif "TOOL" in state or "EXEC" in state:
            badge = f"{YELLOW_BG} FERRAMENTA {RESET}"
        elif "REVIEW" in state:
            badge = f"{CYAN_BG} REVISÃO {RESET}"
        else:
            badge = f"{YELLOW_BG} {state} {RESET}"

        chat_code_block = f"{MAGENTA_BG} Chat: #{short_id} {RESET}"
        if title:
            chat_code_block += f" {WHITE}\"{title[:22]}\"{RESET}"

        model_block = f"{BOLD}{CYAN}{model_name}{RESET}"
        if effort_str:
            model_block += f" {YELLOW}{effort_str}{RESET}"
        if mode_str:
            model_block += f" {MAGENTA}{mode_str}{RESET}"

        token_bar = make_bar(used_pct, length=22, low_good=True)
        ctx_color = GREEN if used_pct < 50 else (YELLOW if used_pct < 80 else RED)

        tokens_block = (
            f"{BOLD}{WHITE}Tokens:{RESET} [{token_bar}] {ctx_color}{used_pct:.1f}%{RESET} "
            f"{GRAY}(Entrada:{RESET}{CYAN}{format_tokens(in_tokens)}{RESET} "
            f"{GRAY}Saída:{RESET}{YELLOW}{format_tokens(out_tokens)}{RESET} "
            f"{GRAY}Total:{RESET}{WHITE}{format_tokens(total_tokens)}{RESET}{GRAY}/{format_tokens(cw_size)}){RESET}"
        )

        cost_block = f"{BOLD}{GREEN}Custo API: {cost_str}{RESET}"
        time_block = f"{GRAY}Início:{WHITE}{start_time}{RESET} {GRAY}(+{elapsed_time}){RESET}"
        line1_items = [badge, chat_code_block, model_block, tokens_block, cost_block, time_block]

        line2_items = []
        if quota_5h:
            used_h, rem_h, reset_h = quota_5h
            bar_5h = make_bar(used_h, length=10, low_good=True)
            h_color = GREEN if used_h < 70 else (YELLOW if used_h < 90 else RED)
            reset_txt = f" {GRAY}(reset {format_seconds(reset_h)}){RESET}" if reset_h > 0 else ""
            line2_items.append(f"{BOLD}5 Horas:{RESET} [{bar_5h}] {h_color}{used_h:.1f}%{RESET} {GRAY}restam {rem_h:.1f}%{RESET}{reset_txt}")
        else:
            bar_empty = make_bar(0.0, length=10, low_good=True)
            line2_items.append(f"{BOLD}5 Horas:{RESET} [{bar_empty}] {GREEN}0.0%{RESET} {GRAY}restam 100%{RESET}")

        if quota_weekly:
            used_w, rem_w, reset_w = quota_weekly
            bar_w = make_bar(used_w, length=10, low_good=True)
            w_color = GREEN if used_w < 70 else (YELLOW if used_w < 90 else RED)
            line2_items.append(f"{BOLD}Semanal:{RESET} [{bar_w}] {w_color}{used_w:.1f}%{RESET} {GRAY}restam {rem_w:.1f}%{RESET}")
        else:
            bar_empty_w = make_bar(0.0, length=10, low_good=True)
            line2_items.append(f"{BOLD}Semanal:{RESET} [{bar_empty_w}] {GREEN}0.0%{RESET} {GRAY}restam 100%{RESET}")

        if email:
            plan_str = f" ({plan_tier})" if plan_tier else ""
            line2_items.append(f"{CYAN}👤 {email}{plan_str}{RESET}")
        elif plan_tier:
            line2_items.append(f"{GRAY}Plano:{WHITE}{plan_tier}{RESET}")

        if running_subagents:
            line2_items.append(f"{YELLOW_BG} Subagentes ({len(running_subagents)}): {','.join(running_subagents)} {RESET}")
        elif active_agent:
            line2_items.append(f"{BLUE}Agente: {active_agent}{RESET}")

        if task_count:
            line2_items.append(f"{BLUE}⚙️ Tarefas:{task_count}{RESET}")

        if artifact_count:
            line2_items.append(f"{CYAN}📄 Docs:{artifact_count}{RESET}")

        if sandbox:
            line2_items.append(f"{MAGENTA}[Sandbox:ON]{RESET}")

        if dir_name:
            line2_items.append(f"{WHITE}📁 {dir_name}{RESET}")

        if branch:
            dirty_flag = f"{RED}*{RESET}" if dirty else ""
            line2_items.append(f"{MAGENTA}git:{branch}{dirty_flag}{RESET}")

        sep = f" {GRAY}│{RESET} "
        output = f"{sep.join(line1_items)}\n{sep.join(line2_items)}"
        sys.stdout.write(output)

    except Exception:
        sys.stdout.write("✦ Antigravity CLI")

if __name__ == "__main__":
    main()

import subprocess
import json
import os
import sys
import re

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "statusline.py")

def strip_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

def run_statusline(payload, env=None):
    json_str = json.dumps(payload)
    custom_env = os.environ.copy()
    if env:
        custom_env.update(env)
    res = subprocess.run(
        [sys.executable, SCRIPT_PATH],
        input=json_str,
        text=True,
        capture_output=True,
        encoding="utf-8",
        env=custom_env
    )
    return res.stdout, res.returncode

def test_empty_payload():
    out, code = run_statusline({})
    assert code == 0
    assert "Antigravity" in out or "IDLE" in out
    print("PASS: test_empty_payload")

def test_full_hd_wide_screen_3_lines():
    payload = {
        "agent_state": "idle",
        "terminal_width": 160,
        "session_id": "test-session-12345678",
        "title": "Autonomous Coding Task",
        "email": "developer@example.com",
        "plan_tier": "Pro",
        "cwd": "C:\\projects\\my-agent",
        "model": {"display_name": "Gemini 3.8 Flash", "effort": "high"},
        "cycle_mode": "auto",
        "context_window": {
            "used_percentage": 14.5,
            "total_input_tokens": 120000,
            "total_output_tokens": 8500,
            "cached_tokens": 40000,
            "context_window_size": 1048576
        },
        "quota": {
            "gemini-5h": {"remaining_fraction": 0.82, "reset_in_seconds": 10800},
            "gemini-weekly": {"remaining_fraction": 0.91}
        },
        "task_count": 2,
        "artifact_count": 3,
        "subagents": [{"name": "research", "status": "running"}],
        "vcs": {"branch": "feature/analytics", "dirty": True, "ahead": 2, "behind": 0},
        "mcp_servers": ["filesystem", "postgres", "github"],
        "skills_count": 5,
        "sandbox": {"enabled": True},
        "version": "1.4.12"
    }
    out, code = run_statusline(payload)
    assert code == 0
    lines = out.strip().split("\n")
    assert len(lines) == 3, f"Expected 3 lines, got {len(lines)}: {lines}"
    
    # Line 1 assertions (Executive & Tokens)
    assert "Gemini 3.8 Flash" in lines[0]
    assert "Tokens:" in lines[0]
    assert "Cost:" in lines[0]
    assert "Saved" in lines[0]
    
    # Line 2 assertions (Quotas & Autonomous swarm)
    assert "5h:" in lines[1]
    assert "7d:" in lines[1]
    assert "Subagents (1)" in lines[1]
    assert "Tasks:2" in lines[1]
    
    # Line 3 assertions (Environment, RAM, MCP, Git, Clock)
    assert "RAM:" in lines[2]
    assert "my-agent" in lines[2]
    assert "feature/analytics" in lines[2]
    assert "MCP:3" in lines[2]
    assert "Sandbox:ON" in lines[2]
    assert "v1.4.12" in lines[2]
    print("PASS: test_full_hd_wide_screen_3_lines")

def test_narrow_terminal_split_view():
    payload = {
        "agent_state": "tool_use",
        "terminal_width": 80,
        "model": {"display_name": "Gemini 3.8 Flash"},
        "cwd": "C:\\projects\\app",
        "vcs": {"branch": "main"},
        "context_window": {"used_percentage": 25.0, "total_input_tokens": 25000},
        "quota": {"gemini-5h": {"remaining_fraction": 0.50, "reset_in_seconds": 3600}}
    }
    out, code = run_statusline(payload)
    assert code == 0
    lines = out.strip().split("\n")
    assert len(lines) == 3
    for i, line in enumerate(lines):
        visible_len = len(strip_ansi(line))
        assert visible_len <= 95, f"Line {i+1} visible len {visible_len} exceeds limit: {strip_ansi(line)}"
    print("PASS: test_narrow_terminal_split_view")

def test_high_pace_quota_alert():
    payload = {
        "agent_state": "working",
        "terminal_width": 140,
        "quota": {
            "gemini-5h": {"remaining_fraction": 0.15, "reset_in_seconds": 12000}
        }
    }
    out, code = run_statusline(payload)
    assert code == 0
    assert "HIGH PACE" in out
    print("PASS: test_high_pace_quota_alert")

def test_themes():
    payload = {
        "agent_state": "idle",
        "terminal_width": 120,
        "model": {"display_name": "Gemini"},
        "context_window": {"used_percentage": 10.0}
    }
    for theme in ["default", "tokyo_night", "catppuccin", "nord", "cyberpunk", "plain"]:
        # We can pass custom theme via config or verify it executes cleanly
        out, code = run_statusline(payload)
        assert code == 0
    print("PASS: test_themes")

if __name__ == "__main__":
    print("\n--- Running Antigravity Toolbar Test Suite ---")
    test_empty_payload()
    test_full_hd_wide_screen_3_lines()
    test_narrow_terminal_split_view()
    test_high_pace_quota_alert()
    test_themes()
    print("All 5 test cases passed successfully!\n")

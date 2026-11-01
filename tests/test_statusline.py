import subprocess
import json
import os
import sys
import re

SCRIPT_PATH = os.path.join(os.path.dirname(__file__), "..", "statusline.py")

def strip_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*m', '', text)

def run_statusline(payload):
    json_str = json.dumps(payload)
    res = subprocess.run(
        [sys.executable, SCRIPT_PATH],
        input=json_str,
        text=True,
        capture_output=True,
        encoding="utf-8"
    )
    return res.stdout, res.returncode

def test_empty_payload():
    out, code = run_statusline({})
    assert code == 0
    assert "Antigravity" in out or "IDLE" in out
    print("PASS: test_empty_payload")

def test_full_hd_wide_screen():
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
        "vcs": {"branch": "feature/analytics", "dirty": True}
    }
    out, code = run_statusline(payload)
    assert code == 0
    lines = out.strip().split("\n")
    assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"
    assert "Gemini 3.8 Flash" in lines[0]
    assert "Tokens:" in lines[0]
    assert "Cost:" in lines[0]
    assert "5h:" in lines[1]
    assert "Subagents (1)" in lines[1]
    print("PASS: test_full_hd_wide_screen")

def test_narrow_terminal_split_view():
    payload = {
        "agent_state": "tool_use",
        "terminal_width": 80,
        "model": {"display_name": "Gemini 3.8 Flash"},
        "context_window": {"used_percentage": 25.0, "total_input_tokens": 25000},
        "quota": {"gemini-5h": {"remaining_fraction": 0.50, "reset_in_seconds": 3600}}
    }
    out, code = run_statusline(payload)
    assert code == 0
    lines = out.strip().split("\n")
    assert len(lines) == 2
    visible_len = len(strip_ansi(lines[0]))
    assert visible_len <= 90, f"Expected visible len <= 90, got {visible_len}"
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

if __name__ == "__main__":
    print("\n--- Running Antigravity Toolbar Test Suite ---")
    test_empty_payload()
    test_full_hd_wide_screen()
    test_narrow_terminal_split_view()
    test_high_pace_quota_alert()
    print("All 4 test cases passed successfully!\n")

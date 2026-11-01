# Antigravity CLI Toolbar (`agy-cli-toolbar`)

An advanced, adaptive **2-line status bar** (responsive across Full HD, medium, and narrow split panes) for the **Google Antigravity CLI (`agy`)**.

Built in **Pure Python (Zero dependencies)** with double-sized 20-block quota bargraphs, terminal auto-resizing, token speed (tokens/sec), prompt caching discounts, dynamic API cost estimation, rolling 5-hour & weekly quota countdowns, subagents, background jobs, themes, and automated one-line installation.

---

## 📸 Preview

### Full HD / Wide Terminals (>= 140 columns)
```text
 IDLE  │  #23afa7c1  "Statusline Customi" │ Gemini 3.8 Flash ⚡high [auto] │ Tokens: [██░░░░░░░░░░░░░░░░░░░░░░] 8.1% (In:81.2k Out:4.2k ⚡cache:30.0k Total:85.4k/1.05M) │ Cost: $0.0598 │ ⚡90.3t/s │ Start:00:31:22 (+15m)
5h: [████░░░░░░░░░░░░░░░░] 21% (2h50m) │ 7d: [██░░░░░░░░░░░░░░░░░░] 12% (106h40m) │ 👤 user@example.com (Pro) │ Subagents (1): research │ ⚙️ Tasks:1 │ 📄 Docs:1 │ 📁 workspace │ git:main* │ v1.4.2
```

### Medium / Split Screen Terminals (100 - 139 columns)
```text
 IDLE  │ #23afa7c1 │ Gemini 3.8 Flash ⚡high [auto] │ Tokens: [███░░░░░░░░░] 21.4% (128.5k) │ Cost: $0.1245 │ Start:00:31:22 (+3m)
5h: [████░░░░░░] 38% (2h42m) │ 7d: [██░░░░░░░░] 18% │ 👤 user@example.com (Pro) │ ⚙️ Tasks:1 │ git:main*
```

### Narrow / Side Panel Terminals (< 100 columns)
```text
 TOOL USE  │ Gemini 3.8 Flash │ Tokens: [██░░░░░░] 25.0% (25.0k)
5h: [███░░░] 50% (1h00m) │ git:main
```

---

## 🚀 Key Features

* **Double-Sized Quota Bargraphs**: Line 2 features extra-wide **20-block graphical gauges** for both 5-hour rolling pool and 7-day weekly quotas.
* **Terminal Auto-Responsiveness**: Dynamically measures terminal width (`terminal_width` or `os.get_terminal_size()`) and scales bargraph lengths and widgets to fit without wrapping.
* **Context Caching & Pricing**: Calculates cost in USD accounting for cached prompt tokens (applying up to 80-90% discount on cache hits).
* **Generation Speed (`t/s`)**: Live tokens/second throughput calculation based on session time.
* **Weekly Reset Countdown**: Displays exact remaining time countdown for weekly quota reset alongside the 5-hour counter.
* **High-Pace Quota Alert**: Flags `[HIGH PACE]` if you are burning through the 5-hour quota too quickly before the reset window.
* **Pure Python & Lightning Fast**: Startup latency of **~50ms**, zero third-party packages, zero Node.js/npm required.
* **Theme Support**: Includes `default`, `tokyo_night`, `catppuccin`, and `plain` (for `NO_COLOR` / light terminals).
* **Configurable via `config.json`**: Toggle widgets on/off without touching Python code.
* **Automatic Session Pruning**: Keeps only the most recent 50 sessions in memory to prevent file bloat.

---

## 🛠️ Automated 1-Click Installation

### Windows (PowerShell)
Clone or download and run:
```powershell
.\install.ps1
```
*Or via one-liner:*
```powershell
irm https://raw.githubusercontent.com/marceloasl99/agy-cli-toolbar/main/install.ps1 | iex
```

### Linux / macOS (Bash)
```bash
chmod +x install.sh && ./install.sh
```
*Or via one-liner:*
```bash
curl -fsSL https://raw.githubusercontent.com/marceloasl99/agy-cli-toolbar/main/install.sh | bash
```

---

## ⚙️ Configuration (`config.json`)

The installer places a configuration file at `~/.antigravity-custom/config.json`:

```json
{
  "show_cost": true,
  "show_tokens_per_sec": true,
  "show_quota_5h": true,
  "show_quota_weekly": true,
  "show_subagents": true,
  "show_tasks": true,
  "show_artifacts": true,
  "show_git": true,
  "show_workspace": true,
  "show_email": true,
  "theme": "default",
  "nerd_fonts": false,
  "max_cached_sessions": 50
}
```

Available themes:
* `"default"`: High-contrast modern ANSI colors.
* `"tokyo_night"`: 24-bit TrueColor Tokyo Night palette.
* `"catppuccin"`: 24-bit TrueColor Catppuccin Mocha palette.
* `"plain"`: Clean text without background fills.

---

## 🧪 Running the Test Suite

We provide a test suite with 4 automated test cases covering wide, medium, and narrow responsive modes, empty payloads, and quota alerts:

```bash
python tests/test_statusline.py
```

---

## 📄 License

MIT License. Free for personal and commercial use.

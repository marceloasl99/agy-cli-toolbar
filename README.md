# Antigravity CLI Toolbar (`agy-cli-toolbar`)

An advanced, high-resolution **2-line status bar** (optimized for 1080p Full HD displays) for the **Google Antigravity CLI (`agy`)**.

Real-time monitoring of agent lifecycle state, context window consumption with graphical bargraphs, prompt input/output/total token breakdown, estimated commercial API costs in USD, 5-hour rolling & weekly quotas with reset countdowns, running subagents, background tasks, Git branch status, and active project workspace directory.

---

## 📸 Preview

```text
 IDLE  │  Chat: #23afa7c1  "Statusline Customizati" │ Gemini 3.8 Flash ⚡high [auto] │ Tokens: [██░░░░░░░░░░░░░░░░░░░░] 7.4% (In:74.2k Out:3.8k Total:78.0k/1.05M) │ API Cost: $0.0699 │ Start:00:31:22 (+3m)
5 Hours: [██░░░░░░░░] 19.0% left 81.0% (reset 3h06m) │ Weekly: [█░░░░░░░░░] 10.0% left 90.0% │ 👤 user@example.com (Pro) │ Subagents (1): research │ ⚙️ Tasks:1 │ 📄 Docs:1 │ 📁 workspace │ git:main*
```

---

## 🚀 Key Features

* **Lifecycle State Badges**: Distinct solid badge colors for ` IDLE `, ` THINKING `, ` TOOL USE `, and ` REVIEWING `.
* **Conversation Identity**: Displays short Chat ID (`#23afa7c1`) and title for easy session resumption with `agy --conversation <ID>`.
* **Model & Reasoning**: Active model name (`Gemini 3.8 Flash`), reasoning effort tier (`⚡high`), and cycle mode (`[auto]`, `[plan]` via `Shift+Tab`).
* **Full HD Token Bargraph**: High-resolution 22-block ASCII progress bar rendering context window saturation (1M+ capacity) with dynamic ANSI color transitions (green <50%, yellow <80%, red >80%).
* **Token Metrics Breakdown**: Detailed breakdown of Input tokens, Output/Thinking tokens, and Total accumulated tokens.
* **Live Commercial API Cost Estimation**: Calculates real-time cost in USD based on standard Google Cloud / Vertex AI pricing per million tokens.
* **Quota Pools & Reset Timers**: Visual bargraph gauges for **5-hour rolling pool** and **Weekly pool**, along with exact time countdowns to quota reset (`reset 3h06m`).
* **Active Subagents & Tasks**: Real-time counter of parallel subagents running and background asynchronous jobs.
* **Workspace & VCS**: Active directory folder name, Git branch, and dirty status indicator (`*`).

---

## 🛠️ Installation & Setup

### 1. Download or Copy the Script

Save `statusline.py` into your user home custom folder:

* **Windows**: `C:\Users\<YOUR_USER>\.antigravity-custom\statusline.py`
* **Linux / macOS**: `~/.antigravity-custom/statusline.py`

### 2. Configure `settings.json`

Open your Antigravity CLI configuration file:
* **Windows**: `C:\Users\<YOUR_USER>\.gemini\antigravity-cli\settings.json`
* **Linux / macOS**: `~/.gemini/antigravity-cli/settings.json`

Add the `"statusLine"` block:

#### Windows:
```json
{
  "statusLine": {
    "type": "command",
    "command": "python C:\\Users\\<YOUR_USER>\\.antigravity-custom\\statusline.py",
    "padding": 0,
    "stack_with_default": false,
    "enabled": true
  }
}
```

#### Linux / macOS:
```json
{
  "statusLine": {
    "type": "command",
    "command": "python3 ~/.antigravity-custom/statusline.py",
    "padding": 0,
    "stack_with_default": false,
    "enabled": true
  }
}
```

> **Important options:**
> * `"padding": 0`: Eliminates blank/black spacing lines above the status bar.
> * `"stack_with_default": false`: Replaces the default statusline to maintain a clean 2-line layout.

### 3. Immediate Activation (Without Restarting)

If you already have an Antigravity CLI terminal open, activate it on the fly by typing:

```bash
/statusline python C:\Users\<YOUR_USER>\.antigravity-custom\statusline.py
```
*(On Linux/macOS use `python3 ~/.antigravity-custom/statusline.py`)*

---

## 📄 License

MIT License. Feel free to modify and adapt to your workflow!

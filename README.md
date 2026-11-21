# Antigravity CLI Toolbar (`agy-cli-toolbar`)

An advanced, adaptive **3-line status bar** (responsive across Full HD, medium, and narrow split panes) for the **Google Antigravity CLI (`agy`)**.

Built in **Pure Python (Zero runtime dependencies)** with sub-character smooth progress bar rendering, double-sized 20-block quota gauges, terminal auto-resizing, token speed (tokens/sec), prompt caching discounts & savings calculation, dynamic API cost estimation in USD, rolling 5-hour & weekly quota countdowns, quota burn rate velocity, subagents, background jobs, host RAM health monitor, MCP servers & skills tooling engine, Git VCS intelligence, themes, and automated 1-click installation.

---

## 📸 Real Terminal Preview

![Antigravity CLI Toolbar Real Terminal Capture](assets/real_terminal_preview.png)

> *Real terminal capture of Google Antigravity CLI v1.4.12 running on Windows with `agy-cli-toolbar` active.*

---

## 🌟 Why Use `agy-cli-toolbar`?

By default, the Antigravity CLI provides minimal status feedback. Alternative statusbars often require Node.js runtimes, wrap awkwardly on narrower screens, or lack critical financial, system health, and rate-limit insights.

`agy-cli-toolbar` is:
* **Zero Dependencies**: Pure Python 3.8+ using only the standard library (no `psutil` or external packages required).
* **Blazing Fast**: Sub-10ms execution latency, never blocking prompt responsiveness.
* **Sub-Character Smooth Progress Bars**: Fractional block rendering (`▏`, `▎`, `▍`, `▌`, `▋`, `▊`, `▉`, `█`) providing pixel-level gauge accuracy.
* **Double-Width Bargraph Gauges**: 24 blocks for context saturation and 20 blocks for 5-hour and 7-day quota pools.
* **Live Commercial API Cost & Savings (USD)**: Automatically calculates what your current session costs under commercial Google Cloud / Vertex AI pricing, including context cache savings.
* **Host RAM & System Health**: Real-time cross-platform memory load monitoring (`🧠 RAM: 56%/23G`).
* **Tooling Ecosystem**: Live counters for loaded MCP servers (`🔌 MCP: 3 active`) and registered skills (`⚡ Skills: 8`).
* **Fully Responsive**: Dynamically scales and trims segments if you split your terminal or open side panels (<100 columns).

---

## 📊 3-Tier Metrics Architecture

```
[ IDLE ]  │ #29bfb6f9 "My Project" │ ✦ Gemini 3.8 Flash ⚡medium [auto] │ Tokens: [██████▍░░░░░░░░░░░░░░░░░] 26.8% (In:165.0k Out:12.4k ⚡cache:54.0k Total:177.4k/1.05M) │ Cost: $0.1399 (Saved $0.0304) │ ⏱ 45m
5h: [█████▎░░░░░░░░░░░░░░] 26% (reset 2h43m) │ 7d: [██▍░░░░░░░░░░░░░░░░░] 12% (120h) │ 🟢 Safe Pace │ 👤 user@dev.io [Pro] │ 🤖 Subagents (1): researcher │ ⚙️ Tasks:1 │ 📄 Docs:4
🧠 RAM: [████▌░░░] 56%/23G │ 🖥️ Windows │ 📁 agy-cli-toolbar │ git:main* +1-0 │ 🔌 MCP:3 active │ ⚡ Skills:8 │ 🛡️ Sandbox:ON │ 🕒 23:16:56 │ agy v1.4.12 • Py3.14
```

### Line 1: AI Reasoning, Model & API Financials
* **Lifecycle Badge**: High-contrast indicator (`IDLE`, `THINKING`, `TOOL USE`, `REVIEWING`, `ERROR`).
* **Chat ID & Title**: Short conversation hash (`#29bfb6f9`) for fast resumption (`agy --conversation <ID>`) and title snippet.
* **Model & Reasoning**: Displays active model (e.g., `✦ Gemini 3.8 Flash`), thinking effort (`⚡medium`/`⚡high`), and cycle mode (`[auto]`/`[plan]`).
* **Context Saturation**: Graphical bargraph with sub-character accuracy, input/output/cache tokens, total capacity, and `[>200k]` alert.
* **API Cost & Cache Savings (USD)**: Real-time estimated billable amount based on standard token pricing, plus exact dollar amount saved via prompt caching.
* **Generation Speed (`t/s`)**: Live throughput counter based on session elapsed time.
* **Session Duration**: Active duration (`⏱ 45m`) and session start timestamp.

### Line 2: Quota Pools, Limits & Autonomous Cluster
* **5-Hour Rolling Limit**: Double-length (20-block) progress bar, percentage used, and exact reset countdown (`reset 2h43m`).
* **7-Day Weekly Limit**: Double-length (20-block) progress bar with weekly reset timer (`120h`).
* **Quota Velocity / Burn Rate**: Real-time pace indicator (`🟢 Safe Pace` vs `🔥 Burn: 28%/h`).
* **Account Info**: User email and subscription tier badge (`[Pro]` / `[Enterprise]`).
* **Autonomous Subagents Swarm**: Real-time counter and named roster of active autonomous subagents.
* **Artifacts & Tasks**: Counter of background async tasks (`⚙️ Tasks`) and conversation documents (`📄 Docs`).

### Line 3: Environment, Workspace & Tooling Engine
* **System RAM Health**: Live host memory pressure gauge and gigabyte capacity (`🧠 RAM: 56%/23G`).
* **Host Operating System**: Detected platform icon (`🖥️ Windows` / `🐧 Linux` / `🍎 macOS`).
* **Workspace Directory**: Project folder name (`📁 agy-cli-toolbar`).
* **Git VCS Intelligence**: Active branch, uncommitted dirty flag (`*`), and ahead/behind commit counts (`+1 -0`).
* **MCP Tooling Ecosystem**: Active MCP servers count (`🔌 MCP: 3 active`).
* **Skills Capabilities**: Registered agent skills count (`⚡ Skills: 8`).
* **Security Perimeter**: Sandbox isolation status (`🛡️ Sandbox: ON` / `Sandbox: OFF`).
* **Local Real-Time Clock**: Live system timestamp with seconds precision (`🕒 23:16:56`).
* **Engine & Runtime**: CLI binary version and Python runtime (`agy v1.4.12 • Py3.14`).

---

## 🛠️ Quick Installation

### Option 1: Automated 1-Click Installer (Recommended)

#### Windows (PowerShell):
```powershell
irm https://raw.githubusercontent.com/marceloasl99/agy-cli-toolbar/main/install.ps1 | iex
```

#### Linux / macOS (Bash):
```bash
curl -fsSL https://raw.githubusercontent.com/marceloasl99/agy-cli-toolbar/main/install.sh | bash
```

---

### Option 2: Manual Installation

1. Create directory `~/.antigravity-custom` and copy `statusline.py` into it.
2. Open your Antigravity CLI configuration file:
   * **Windows**: `C:\Users\<YOUR_USER>\.gemini\antigravity-cli\settings.json`
   * **Linux/macOS**: `~/.gemini/antigravity-cli/settings.json`
3. Add the `statusLine` configuration block:

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

> **Important flags:**
> * `"padding": 0`: Eliminates blank/black spacing rows above the status line.
> * `"stack_with_default": false`: Replaces the default CLI footer for a clean layout.

---

## 🎮 Immediate Testing (No Restart Needed)

If you already have a terminal session open with Antigravity CLI, toggle the statusline on the fly:

```bash
/statusline python C:\Users\<YOUR_USER>\.antigravity-custom\statusline.py
```

---

## 👥 Gerenciador de Perfis & Quotas Multi-Contas (`agy-profile`)

O `agy-cli-toolbar` inclui uma ferramenta completa para gerenciar múltiplas contas do Google, alternar perfis e acompanhar as cotas (5h e 7d) de cada conta isoladamente.

### Comandos Rápidos:

| Comando | Descrição |
| :--- | :--- |
| `agy-profile` | Abre o **Menu Interativo** colorido para gerenciar perfis |
| `agy-profile list` | Lista todos os perfis com email, status OAuth e **gráficos de cota (5h / 7d)** |
| `agy-profile switch <num\|nome>` | Alterna o perfil ativo no sistema e sincroniza as credenciais globais |
| `agy-profile create <nome> [email]` | Cria um novo perfil isolado com estrutura `.gemini` e atalhos |
| `agy-profile auth <num\|nome>` | Inicia o fluxo de autenticação **OAuth 2.0** do Google |
| `agy-profile desktop <num\|nome>` | Abre o **Antigravity Desktop** isolado no perfil escolhido |
| `agy-profile run <num\|nome> [args]` | Executa o `agy` CLI isolado nas variáveis de ambiente do perfil |
| `agy-profile tray` (ou `agy-tray`) | Inicia o **App da Bandeja do Sistema (Tray)** e o **Widget Flutuante do Desktop** |
| `agy-profile autostart on` | Ativa a inicialização automática silenciosa do Tray ao ligar o Windows |

### 🖥️ Windows Tray App & Desktop Widget Flutuante

O aplicativo de bandeja (`tray_app.pyw`) roda em segundo plano sem janela de console e oferece:
* **Ícone na Bandeja (Tray)**: Ao lado do relógio do Windows com menu de contexto de acesso rápido a cada conta.
* **Widget Flutuante Moderno & Painel de Configurações**:
  - **Botão `⚙️ Config`**: Permite personalizar em tempo real:
    - **Grade e Disposição (Todos os Presets)**: `1x1`, `2x1`, `1x2`, `2x2`, `3x1`, `1x3`, `2x3`, `3x2`, `4x1`, `1x4`, `2x4`, `4x2`, `1x5`, `5x1`, `3x3`.
    - **Tempo de Atualização (Refresh)**: De 5 a 60 segundos com atualização 100% livre de cintilação (in-place redraw).
    - **Opacidade da Janela**: Ajuste de transparência de 70% a 100%.
    - **Ativar / Desativar Perfis**: Escolha quais perfis exibir ou ocultar com caixas de seleção.
    - **Reordenar Blocos**: Botões `▲ Subir` e `▼ Descer` no menu, além das setas rápidas `◀` e `▶` no próprio cartão.
  - **Redimensionamento Livre (Resize Grip `◢`)**: Alça de arrastar no canto inferior direito para redimensionar a janela para qualquer tamanho desejado.
  - **Barras de Cota Detalhadas**: Exibe `% usada` e `% livre` tanto na barra quanto no texto (`5h: 12.7% usada │ 87.3% livre`).
  - **Clique para Abrir o CMD**: Botão `⚡ Abrir CMD (agy<N>)` para abrir o terminal diretamente configurado no perfil correspondente.
  - **Fixar / Destravar (`🔒 Fixado` / `🔓 Mover`)**: Botão no cabeçalho para travar a posição na tela ou destravar para arrastar.

Para iniciar o app:
```powershell
agy-tray
```
*(Ou através de `agy-profile tray`)*

---

### 🔑 Autenticação com OAuth 2.0
Ao executar `agy-profile auth <nome>`, você pode escolher:
1. **Navegador Web (Servidor Local)**: Inicia um servidor HTTP local na porta `8085` com PKCE (RFC 7636), abre o navegador no login oficial do Google e grava automaticamente `oauth_creds.json` e `google_accounts.json`.
2. **Antigravity Desktop (1-Clique)**: Abre o app desktop com diretório de dados isolado para login nativo.
3. **Copiar Credenciais**: Duplica as credenciais de outro perfil existente.

---

## ⚙️ Customization (`config.json`)

Customize widgets and aesthetics in `~/.antigravity-custom/config.json`:

```json
{
  "theme": "default",
  "nerd_fonts": false,
  "smooth_bars": true,
  "show_line3": true,
  "show_cost": true,
  "show_tokens_per_sec": true,
  "show_quota_5h": true,
  "show_quota_weekly": true,
  "show_burn_rate": true,
  "show_subagents": true,
  "show_tasks": true,
  "show_artifacts": true,
  "show_email": true,
  "show_ram": true,
  "show_workspace": true,
  "show_git": true,
  "show_mcp": true,
  "show_skills": true,
  "show_sandbox": true,
  "show_clock": true,
  "show_version": true
}
```

### Available Color Themes:
* `"default"`: High-contrast vibrant modern ANSI colors.
* `"tokyo_night"`: 24-bit TrueColor Tokyo Night palette.
* `"catppuccin"`: 24-bit TrueColor Catppuccin Mocha palette.
* `"nord"`: 24-bit TrueColor Nord Arctic ice-blue palette.
* `"cyberpunk"`: 24-bit TrueColor Neon Cyberpunk palette.
* `"plain"`: Clean text mode without background fills (supports `NO_COLOR`).

---

## 🧪 Automated Tests

Run the built-in test suite verifying 3-line layout and responsive scaling:

```bash
python tests/test_statusline.py
```

---

## 📄 License

MIT License. Free for personal and commercial usage.

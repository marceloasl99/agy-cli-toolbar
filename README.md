# Antigravity CLI Toolbar (agy-cli-toolbar)

Barra de status avançada de **2 linhas em alta resolução** (otimizada para Full HD) para o **Google Antigravity CLI (`agy`)**.

Exibe em tempo real o status de processamento, tokens (entrada/saída/total), janela de contexto com bargraph gráfico, estimativa de custo da API em dólares, cota de 5 horas e semanal com tempo de reset, subagentes ativos, tarefas em background, repositório Git e diretório atual.

---

## 📸 Pré-visualização

```text
 IDLE  │  Chat: #23afa7c1  "Statusline Customizati" │ Gemini 3.8 Flash ⚡high [auto] │ Tokens: [██░░░░░░░░░░░░░░░░░░░░] 7.4% (Entrada:74.2k Saída:3.8k Total:78.0k/1.05M) │ Custo API: $0.0699 │ Início:00:31:22 (+3m)
5 Horas: [██░░░░░░░░] 19.0% restam 81.0% (reset 3h06m) │ Semanal: [█░░░░░░░░░] 10.0% restam 90.0% │ 👤 user@example.com (Pro) │ Subagentes (1): research │ ⚙️ Tarefas:1 │ 📄 Docs:1 │ 📁 workspace │ git:main*
```

---

## 🚀 Recursos

* **Badge de Estado**: ` IDLE `, ` PENSANDO `, ` FERRAMENTA `, ` REVISÃO ` em destaque com cores de fundo sólidas.
* **Código do Chat**: Mostra o ID curto do chat atual (`#23afa7c1`) e o título da conversa.
* **Modelo & Raciocínio**: Nome do modelo (`Gemini 3.8 Flash`), esforço de raciocínio (`⚡high`) e modo de ciclo (`[auto]`, `[plan]`).
* **Bargraph de Tokens em Full HD**: Barra gráfica de alta resolução indicando o percentual de preenchimento da janela de 1M+ tokens.
* **Detalhamento de Tokens**: Tokens de Entrada, Saída e Total acumulado.
* **Estimativa de Custo API (USD)**: Calcula em tempo real o custo equivalente da chamada de API comercial (Input + Output/Reasoning).
* **Cotas (5 Horas e Semanal)**: Barras visuais de consumo com contagem regressiva para o reset de cota (`reset 3h06m`).
* **Sessão & Tempo**: Horário em que a sessão começou e tempo ativo decorrido.
* **Subagentes & Tarefas**: Monitoramento de agentes paralelos rodando e tarefas assíncronas em segundo plano.
* **Workspace & Git**: Pasta do projeto, branch atual e indicador de modificações (`*`).

---

## 🛠️ Como Instalar e Configurar

### 1. Salvar o Script

Copie o arquivo `statusline.py` para a pasta `.antigravity-custom` na sua pasta de usuário:

* **Windows**: `C:\Users\<SEU_USUARIO>\.antigravity-custom\statusline.py`
* **Linux/macOS**: `~/.antigravity-custom/statusline.py`

### 2. Configurar o `settings.json` do Antigravity CLI

Abra o arquivo de configuração do CLI:
* **Windows**: `C:\Users\<SEU_USUARIO>\.gemini\antigravity-cli\settings.json`
* **Linux/macOS**: `~/.gemini/antigravity-cli/settings.json`

Adicione o bloco `"statusLine"`:

#### No Windows:
```json
{
  "statusLine": {
    "type": "command",
    "command": "python C:\\Users\\<SEU_USUARIO>\\.antigravity-custom\\statusline.py",
    "padding": 0,
    "stack_with_default": false,
    "enabled": true
  }
}
```

#### No Linux / macOS:
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

> **Dicas:**
> * `"padding": 0`: remove linhas em branco extras acima da barra.
> * `"stack_with_default": false`: substitui a barra padrão para manter apenas as 2 linhas limpas.

### 3. Ativação Imediata (Sem reiniciar)

Se já estiver com o Antigravity CLI aberto no terminal, ative na mesma hora rodando:

```bash
/statusline python C:\Users\<SEU_USUARIO>\.antigravity-custom\statusline.py
```
*(No Linux/macOS use `python3 ~/.antigravity-custom/statusline.py`)*

---

## 📄 Licença

MIT License. Sinta-se livre para customizar e expandir!

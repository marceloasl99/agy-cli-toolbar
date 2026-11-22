import os
import sys
import json
import time
import socket
import threading
import subprocess
import traceback
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageDraw

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOM_DIR = os.path.join(os.path.expanduser("~"), ".antigravity-custom")
for d in [SCRIPT_DIR, CUSTOM_DIR]:
    if d not in sys.path:
        sys.path.insert(0, d)

def _global_exception_handler(exctype, value, tb):
    if issubclass(exctype, (KeyboardInterrupt, SystemExit)):
        sys.__excepthook__(exctype, value, tb)
        return
    try:
        os.makedirs(CUSTOM_DIR, exist_ok=True)
        log_path = os.path.join(CUSTOM_DIR, "tray.log")
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] EXCEÇÃO NÃO TRATADA:\n")
            f.write("".join(traceback.format_exception(exctype, value, tb)))
            f.write("\n")
    except Exception:
        pass

sys.excepthook = _global_exception_handler
if hasattr(threading, "excepthook"):
    threading.excepthook = lambda args: _global_exception_handler(args.exc_type, args.exc_value, args.exc_traceback)

try:
    import profile_manager as pm
except ImportError:
    import profile_manager as pm

import pystray
from pystray import MenuItem as item, Menu

CONFIG_FILE = os.path.join(CUSTOM_DIR, "widget_config.json")
SINGLE_INSTANCE_PORT = 49285
SINGLE_INSTANCE_MUTEX = "Local\\AntigravityQuotaMonitor_SingleInstanceMutex"

GRID_PRESETS = {
    "1x1": (1, 1),
    "2x1": (2, 1),
    "1x2": (1, 2),
    "2x2": (2, 2),
    "3x1": (3, 1),
    "1x3": (1, 3),
    "2x3": (2, 3),
    "3x2": (3, 2),
    "4x1": (4, 1),
    "1x4": (1, 4),
    "2x4": (2, 4),
    "4x2": (4, 2),
    "5x1": (5, 1),
    "1x5": (1, 5),
    "3x3": (3, 3)
}

THEMES = {
    "Dark Slate": {
        "name": "Dark Slate",
        "bg": "#0f172a",
        "header_bg": "#1e293b",
        "footer_bg": "#1e293b",
        "card_bg": "#1e293b",
        "card_active_bg": "#172554",
        "card_border": "#334155",
        "card_active_border": "#38bdf8",
        "accent": "#38bdf8",
        "text": "#f8fafc",
        "text_muted": "#94a3b8",
        "bar_bg": "#334155",
        "tag_bg": "#0c4a6e",
        "tag_fg": "#38bdf8"
    },
    "Midnight OLED": {
        "name": "Midnight OLED",
        "bg": "#000000",
        "header_bg": "#0a0a0a",
        "footer_bg": "#0a0a0a",
        "card_bg": "#121212",
        "card_active_bg": "#181824",
        "card_border": "#262626",
        "card_active_border": "#60a5fa",
        "accent": "#60a5fa",
        "text": "#ffffff",
        "text_muted": "#a3a3a3",
        "bar_bg": "#262626",
        "tag_bg": "#1e3a8a",
        "tag_fg": "#93c5fd"
    },
    "Cyberpunk Neon": {
        "name": "Cyberpunk Neon",
        "bg": "#0d0221",
        "header_bg": "#19053b",
        "footer_bg": "#19053b",
        "card_bg": "#19053b",
        "card_active_bg": "#2c0957",
        "card_border": "#4c1d95",
        "card_active_border": "#f43f5e",
        "accent": "#f43f5e",
        "text": "#fdf4ff",
        "text_muted": "#c084fc",
        "bar_bg": "#3b0764",
        "tag_bg": "#831843",
        "tag_fg": "#fb7185"
    },
    "Emerald Tech": {
        "name": "Emerald Tech",
        "bg": "#022c22",
        "header_bg": "#064e3b",
        "footer_bg": "#064e3b",
        "card_bg": "#064e3b",
        "card_active_bg": "#065f46",
        "card_border": "#047857",
        "card_active_border": "#34d399",
        "accent": "#34d399",
        "text": "#ecfdf5",
        "text_muted": "#6ee7b7",
        "bar_bg": "#047857",
        "tag_bg": "#064e3b",
        "tag_fg": "#6ee7b7"
    }
}

DEFAULT_WIDGET_CONFIG = {
    "x": 100,
    "y": 100,
    "width": 820,
    "height": 560,
    "always_on_top": True,
    "visible": True,
    "locked": False,
    "grid_preset": "2x2",
    "columns": 2,
    "refresh_seconds": 15,
    "opacity": 0.96,
    "theme": "Dark Slate",
    "privacy_mode": False,
    "default_expanded": False,
    "card_density": "compact",
    "alert_threshold": 85,
    "show_free_pct": True,
    "show_countdown": True,
    "ui_scale": 1.20,
    "font_size_offset": 1,
    "enabled_profiles": {},
    "profile_order": [],
    "profile_nicknames": {},
    "profile_positions": {},
    "profile_models": {
        "perfil1": ["Gemini 3.8 Flash (High)", "Claude Sonnet 4.6 (Thinking)", "GPT-OSS 120B (Medium)"],
        "perfil2": ["Gemini 3.8 Flash (High)", "Claude Sonnet 4.6 (Thinking)", "GPT-OSS 120B (Medium)"],
        "perfil3": ["Gemini 3.8 Flash (High)", "Claude Sonnet 4.6 (Thinking)", "GPT-OSS 120B (Medium)"],
        "perfil4": ["Gemini 4 Argon (High)", "Gemini 3.8 Flash (High)", "Claude Sonnet 4.6 (Thinking)", "GPT-OSS 120B (Medium)"]
    }
}

def load_widget_config():
    conf = DEFAULT_WIDGET_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                conf.update(json.load(f))
        except Exception:
            pass
    return conf

def save_widget_config(conf):
    try:
        os.makedirs(CUSTOM_DIR, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(conf, f, indent=2)
    except Exception:
        pass

def is_autostart_enabled():
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
        val, _ = winreg.QueryValueEx(key, "AntigravityQuotaMonitor")
        winreg.CloseKey(key)
        return bool(val)
    except Exception:
        return False

def set_autostart(enable=True):
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_SET_VALUE)
        if enable:
            pythonw = sys.executable.replace("python.exe", "pythonw.exe")
            target_script = os.path.join(CUSTOM_DIR, "tray_app.pyw")
            cmd = f'"{pythonw}" "{target_script}"'
            winreg.SetValueEx(key, "AntigravityQuotaMonitor", 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, "AntigravityQuotaMonitor")
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False

def mask_email(email):
    if not email or "@" not in email:
        return email
    parts = email.split("@")
    user, domain = parts[0], parts[1]
    if len(user) <= 3:
        masked_user = user[0] + "***"
    else:
        masked_user = user[:3] + "***" + user[-1]
    return f"{masked_user}@{domain}"

def get_profile_cli_command(profile_key):
    if profile_key == "perfil1":
        return "agy"
    if profile_key.startswith("perfil") and profile_key[6:].isdigit():
        return f"agy{profile_key[6:]}"
    if profile_key.isdigit():
        return f"agy{profile_key}" if profile_key != "1" else "agy"
    return f"agy-{profile_key}"

def open_cmd_for_profile(profile_key):
    pm.pre_run(profile_key)
    cmd_name = get_profile_cli_command(profile_key)
    profiles = pm.discover_profiles()
    prof = profiles.get(profile_key, {})
    disp = prof.get("display", profile_key.upper())

    startup_line = (
        f'title Antigravity CLI [{disp}] && '
        f'echo ======================================================== && '
        f'echo   ANTIGRAVITY CLI - {disp} && '
        f'echo   Comando: {cmd_name} && '
        f'echo ======================================================== && '
        f'echo. && {cmd_name}'
    )
    subprocess.Popen(f'start cmd.exe /k "{startup_line}"', shell=True)

def open_folder(path):
    if os.path.exists(path):
        os.startfile(path)
    else:
        messagebox.showinfo("Pasta não encontrada", f"O diretório não existe:\n{path}")

def create_tray_image(color=(56, 189, 248)):
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, 60, 60], radius=14, fill=(15, 23, 42, 240), outline=color, width=3)
    d.ellipse([20, 20, 44, 44], fill=color)
    d.ellipse([26, 26, 38, 38], fill=(15, 23, 42))
    d.ellipse([29, 29, 35, 35], fill=color)
    return img

class ToolTip:
    """Floating styled tooltip that appears on hover with rich quota model info."""
    def __init__(self, widget, text_func):
        self.widget = widget
        self.text_func = text_func
        self.tip_window = None
        self.widget.bind("<Enter>", self.show_tip)
        self.widget.bind("<Leave>", self.hide_tip)
        self.widget.bind("<ButtonPress>", self.hide_tip)

    def show_tip(self, event=None):
        if self.tip_window:
            return
        text = self.text_func() if callable(self.text_func) else self.text_func
        if not text:
            return
        x = self.widget.winfo_rootx() + 15
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 4
        self.tip_window = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        tw.attributes("-topmost", True)
        frame = tk.Frame(tw, bg="#0b1120", bd=1, relief="solid", highlightbackground="#38bdf8", highlightthickness=1)
        frame.pack(fill="both", expand=True)
        label = tk.Label(frame, text=text, justify="left", font=("Segoe UI", 8),
                         bg="#0b1120", fg="#f8fafc", padx=10, pady=8)
        label.pack()

    def hide_tip(self, event=None):
        if self.tip_window:
            try:
                self.tip_window.destroy()
            except Exception:
                pass
            self.tip_window = None

class ScrollableFrame(tk.Frame):
    """Reusable scrollable frame ensuring all config contents fit on any screen."""
    def __init__(self, parent, bg="#0f172a"):
        super().__init__(parent, bg=bg)
        self.canvas = tk.Canvas(self, bg=bg, bd=0, highlightthickness=0)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_window = tk.Frame(self.canvas, bg=bg)

        self.scrollable_window.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_frame_id = self.canvas.create_window((0, 0), window=self.scrollable_window, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        self.bind_mousewheel(self)

    def _on_canvas_configure(self, event):
        self.canvas.itemconfig(self.canvas_frame_id, width=event.width)

    def bind_mousewheel(self, widget):
        widget.bind("<MouseWheel>", self._on_mousewheel)
        for child in widget.winfo_children():
            self.bind_mousewheel(child)

    def _on_mousewheel(self, event):
        if self.canvas.winfo_exists():
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

class ResizeGrip(tk.Label):
    def __init__(self, parent, target_window):
        super().__init__(parent, text="◢", font=("Segoe UI", 11), fg="#64748b", bg="#1e293b", cursor="size_nw_se")
        self.target = target_window
        self.bind("<ButtonPress-1>", self.on_press)
        self.bind("<B1-Motion>", self.on_motion)
        self.bind("<ButtonRelease-1>", self.on_release)

    def on_press(self, event):
        self.start_x = event.x_root
        self.start_y = event.y_root
        self.start_w = self.target.winfo_width()
        self.start_h = self.target.winfo_height()

    def on_motion(self, event):
        dx = event.x_root - self.start_x
        dy = event.y_root - self.start_y
        new_w = max(self.start_w + dx, 340)
        new_h = max(self.start_h + dy, 220)
        self.target.geometry(f"{new_w}x{new_h}")

    def on_release(self, event):
        self.target.config_data["width"] = self.target.winfo_width()
        self.target.config_data["height"] = self.target.winfo_height()
        save_widget_config(self.target.config_data)

class SettingsDialog(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Configurações Avançadas - Antigravity Quota Manager")
        self.geometry("880x640")
        self.minsize(760, 520)
        self.configure(bg="#0f172a")
        self.attributes("-topmost", True)

        self.config_copy = json.loads(json.dumps(parent.config_data))
        self.current_tab = "appearance"
        self.tab_buttons = {}
        self.tab_frames = {}

        self.build_ui()

    def build_ui(self):
        # 1. Header Bar
        h = tk.Frame(self, bg="#1e293b", height=50)
        h.pack(fill="x")
        
        tk.Label(h, text="⚙️  Centro de Configurações Antigravity", font=("Segoe UI", 12, "bold"), fg="#f8fafc", bg="#1e293b").pack(side="left", padx=16, pady=12)
        tk.Label(h, text="v2.5 Pro", font=("Segoe UI", 8, "bold"), fg="#38bdf8", bg="#0c4a6e", padx=6, pady=2).pack(side="left", padx=6)

        # 2. Main Body: Left Sidebar + Right Content Area
        body = tk.Frame(self, bg="#0f172a")
        body.pack(fill="both", expand=True)

        # Sidebar
        sidebar = tk.Frame(body, bg="#0b1120", width=195)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Nav categories
        tabs = [
            ("appearance", "🎨  Aparência & Grade"),
            ("profiles", "👥  Perfis & Ordem"),
            ("quotas", "⏱️  Cotas & Alertas"),
            ("system", "💻  Sistema & Windows"),
            ("about", "ℹ️  Sobre & Diagnóstico")
        ]

        tk.Label(sidebar, text="PREFERÊNCIAS", font=("Segoe UI", 7, "bold"), fg="#475569", bg="#0b1120").pack(anchor="w", padx=16, pady=(16, 6))

        for tab_id, tab_label in tabs:
            btn = tk.Button(
                sidebar, text=tab_label, font=("Segoe UI", 9), anchor="w",
                fg="#94a3b8", bg="#0b1120", activebackground="#1e293b", activeforeground="#f8fafc",
                bd=0, padx=14, pady=8, cursor="hand2",
                command=lambda tid=tab_id: self.switch_tab(tid)
            )
            btn.pack(fill="x", padx=6, pady=2)
            self.tab_buttons[tab_id] = btn

        # Content Container (Hosts the active ScrollableFrame)
        self.content_container = tk.Frame(body, bg="#0f172a")
        self.content_container.pack(side="right", fill="both", expand=True, padx=14, pady=10)

        # Build each tab view using ScrollableFrame
        self.build_tab_appearance()
        self.build_tab_profiles()
        self.build_tab_quotas()
        self.build_tab_system()
        self.build_tab_about()

        # 3. Bottom Action Bar
        f_act = tk.Frame(self, bg="#1e293b", height=50)
        f_act.pack(fill="x", side="bottom")

        tk.Button(f_act, text="Salvar e Aplicar", font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#0284c7",
                  activebackground="#0369a1", activeforeground="#ffffff", bd=0, padx=18, pady=6, cursor="hand2",
                  command=self.save_and_apply).pack(side="right", padx=16, pady=10)

        tk.Button(f_act, text="Cancelar", font=("Segoe UI", 9), fg="#94a3b8", bg="#1e293b",
                  bd=0, padx=12, pady=6, cursor="hand2", command=self.destroy).pack(side="right", padx=6, pady=10)

        # Activate initial tab
        self.switch_tab("appearance")

    def switch_tab(self, tab_id):
        self.current_tab = tab_id
        for tid, btn in self.tab_buttons.items():
            if tid == tab_id:
                btn.config(fg="#38bdf8", bg="#1e293b", font=("Segoe UI", 9, "bold"))
            else:
                btn.config(fg="#94a3b8", bg="#0b1120", font=("Segoe UI", 9))

        for tid, frame in self.tab_frames.items():
            if tid == tab_id:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    # ---------------- TAB: APARÊNCIA & GRADE ----------------
    def build_tab_appearance(self):
        sf = ScrollableFrame(self.content_container, bg="#0f172a")
        self.tab_frames["appearance"] = sf
        f = sf.scrollable_window

        tk.Label(f, text="Aparência Visual & Layout", font=("Segoe UI", 12, "bold"), fg="#f8fafc", bg="#0f172a").pack(anchor="w", pady=(0, 4))
        tk.Label(f, text="Personalize o formato da grade, temas, zoom e modo de detalhamento dos cartões.", font=("Segoe UI", 8), fg="#64748b", bg="#0f172a").pack(anchor="w", pady=(0, 14))

        # Presets Buttons Grid
        tk.Label(f, text="📐 Presets de Grade Rápidos:", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w")
        
        f_presets = tk.Frame(f, bg="#0f172a")
        f_presets.pack(fill="x", pady=6)

        popular_presets = ["2x2", "1x4", "4x1", "1x2", "2x1", "2x3", "3x2", "1x1", "1x5", "3x3"]
        self.preset_var = tk.StringVar(value=self.config_copy.get("grid_preset", "2x2"))
        self.preset_buttons = {}

        row_f = None
        for i, p in enumerate(popular_presets):
            if i % 5 == 0:
                row_f = tk.Frame(f_presets, bg="#0f172a")
                row_f.pack(fill="x", pady=2)
            
            is_sel = (p == self.preset_var.get())
            b = tk.Button(
                row_f, text=p, font=("Segoe UI", 8, "bold"), width=6,
                fg="#ffffff" if is_sel else "#94a3b8",
                bg="#0284c7" if is_sel else "#1e293b",
                activebackground="#0369a1", bd=0, padx=6, pady=4, cursor="hand2",
                command=lambda val=p: self.select_preset(val)
            )
            b.pack(side="left", padx=3)
            self.preset_buttons[p] = b

        # Theme Selector
        tk.Label(f, text="🎨 Tema de Cores:", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w", pady=(12, 4))
        self.theme_var = tk.StringVar(value=self.config_copy.get("theme", "Dark Slate"))
        cb_theme = ttk.Combobox(f, textvariable=self.theme_var, values=list(THEMES.keys()), state="readonly", width=24, font=("Segoe UI", 9))
        cb_theme.pack(anchor="w")

        # Opacity Slider
        tk.Label(f, text="✨ Opacidade da Janela:", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w", pady=(14, 2))
        f_op = tk.Frame(f, bg="#0f172a")
        f_op.pack(fill="x")

        cur_op = int(self.config_copy.get("opacity", 0.96) * 100)
        self.op_var = tk.IntVar(value=cur_op)
        self.op_lbl = tk.Label(f_op, text=f"{cur_op}%", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a", width=5)
        self.op_lbl.pack(side="right")

        scale_op = tk.Scale(f_op, from_=60, to=100, orient="horizontal", variable=self.op_var, bg="#1e293b", fg="#f8fafc",
                            highlightthickness=0, bd=0, activebackground="#38bdf8", command=lambda v: self.op_lbl.config(text=f"{v}%"))
        scale_op.pack(fill="x", side="left", expand=True)

        # Privacy Mode (Streamer mode)
        f_priv = tk.Frame(f, bg="#0f172a")
        f_priv.pack(fill="x", pady=(14, 4))
        self.priv_var = tk.BooleanVar(value=self.config_copy.get("privacy_mode", False))
        tk.Checkbutton(f_priv, text="Modo Privacidade (Ocultar emails nos cartões para gravação / streaming)",
                       variable=self.priv_var, font=("Segoe UI", 9), fg="#e2e8f0", bg="#0f172a",
                       selectcolor="#1e293b", activebackground="#0f172a", activeforeground="#e2e8f0").pack(anchor="w")

        # Expand / Detail Default Mode
        f_detail = tk.Frame(f, bg="#0f172a")
        f_detail.pack(fill="x", pady=(4, 4))
        self.default_expanded_var = tk.BooleanVar(value=self.config_copy.get("default_expanded", False))
        tk.Checkbutton(f_detail, text="Abrir cartões no Modo Detalhado (Mostra modelos cobertos diretamente)",
                       variable=self.default_expanded_var, font=("Segoe UI", 9), fg="#e2e8f0", bg="#0f172a",
                       selectcolor="#1e293b", activebackground="#0f172a", activeforeground="#e2e8f0").pack(anchor="w")

        # Density preference
        self.density_var = tk.StringVar(value=self.config_copy.get("card_density", "compact"))

        # Zoom & Font Size Adjustment
        tk.Label(f, text="🔍 Zoom da Interface (Escala Geral):", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w", pady=(14, 2))
        f_zoom = tk.Frame(f, bg="#0f172a")
        f_zoom.pack(fill="x")

        cur_zoom = int(round(float(self.config_copy.get("ui_scale", 1.20)) * 100))
        self.zoom_var = tk.IntVar(value=cur_zoom)
        self.zoom_val_lbl = tk.Label(f_zoom, text=f"{cur_zoom}%", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a", width=5)
        self.zoom_val_lbl.pack(side="right")

        scale_zoom = tk.Scale(f_zoom, from_=75, to=200, orient="horizontal", variable=self.zoom_var, bg="#1e293b", fg="#f8fafc",
                              highlightthickness=0, bd=0, activebackground="#38bdf8",
                              command=lambda v: self.zoom_val_lbl.config(text=f"{v}%"))
        scale_zoom.pack(fill="x", side="left", expand=True)

        f_z_presets = tk.Frame(f, bg="#0f172a")
        f_z_presets.pack(fill="x", pady=(2, 6))
        for z_pct, z_label in [(80, "80%"), (100, "100%"), (115, "115%"), (130, "130%"), (150, "150%"), (175, "175%"), (200, "200%")]:
            tk.Button(f_z_presets, text=z_label, font=("Segoe UI", 7, "bold"), fg="#cbd5e1", bg="#1e293b",
                      activebackground="#0284c7", bd=0, padx=6, pady=2, cursor="hand2",
                      command=lambda val=z_pct: self.apply_zoom_preset(val)).pack(side="left", padx=2)

        tk.Label(f, text="🔤 Tamanho da Fonte (Ajuste Fino):", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w", pady=(10, 2))
        f_fnt = tk.Frame(f, bg="#0f172a")
        f_fnt.pack(fill="x", pady=(2, 10))
        self.font_offset_var = tk.IntVar(value=int(self.config_copy.get("font_size_offset", 1)))
        
        font_options = [
            (-1, "Pequena (-1)"),
            (0, "Normal (0)"),
            (1, "Média (+1)"),
            (2, "Grande (+2)"),
            (3, "Extra Grande (+3)")
        ]
        for val, label in font_options:
            tk.Radiobutton(f_fnt, text=label, variable=self.font_offset_var, value=val,
                           font=("Segoe UI", 8), fg="#cbd5e1", bg="#0f172a", selectcolor="#1e293b").pack(side="left", padx=(0, 6))

        sf.bind_mousewheel(f)

    def apply_zoom_preset(self, val):
        self.zoom_var.set(val)
        self.zoom_val_lbl.config(text=f"{val}%")

    def select_preset(self, p):
        self.preset_var.set(p)
        for name, btn in self.preset_buttons.items():
            if name == p:
                btn.config(bg="#0284c7", fg="#ffffff")
            else:
                btn.config(bg="#1e293b", fg="#94a3b8")

    # ---------------- TAB: PERFIS & ORDEM ----------------
    def build_tab_profiles(self):
        sf = ScrollableFrame(self.content_container, bg="#0f172a")
        self.tab_frames["profiles"] = sf
        f = sf.scrollable_window

        tk.Label(f, text="Gerenciador de Perfis", font=("Segoe UI", 12, "bold"), fg="#f8fafc", bg="#0f172a").pack(anchor="w", pady=(0, 4))
        tk.Label(f, text="Organize a sequência dos blocos, altere apelidos e ative o plano Pro (Argon).", font=("Segoe UI", 8), fg="#64748b", bg="#0f172a").pack(anchor="w", pady=(0, 10))

        # Main horizontal container
        f_box = tk.Frame(f, bg="#0f172a")
        f_box.pack(fill="x", expand=True)

        all_profiles = pm.discover_profiles()
        saved_order = self.config_copy.get("profile_order", [])
        self.ordered_keys = [k for k in saved_order if k in all_profiles]
        for k in all_profiles:
            if k not in self.ordered_keys:
                self.ordered_keys.append(k)

        # Listbox
        self.prof_listbox = tk.Listbox(
            f_box, font=("Segoe UI", 9), bg="#1e293b", fg="#f8fafc", selectbackground="#0284c7",
            selectforeground="#ffffff", bd=1, relief="solid", highlightthickness=0, height=8
        )
        self.prof_listbox.pack(side="left", fill="both", expand=True)

        # Action Buttons Column
        f_btns = tk.Frame(f_box, bg="#0f172a")
        f_btns.pack(side="right", fill="y", padx=(10, 0))

        tk.Button(f_btns, text="▲ Subir", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg="#334155", bd=0, padx=12, pady=3, cursor="hand2", command=self.move_prof_up).pack(fill="x", pady=2)
        tk.Button(f_btns, text="▼ Descer", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg="#334155", bd=0, padx=12, pady=3, cursor="hand2", command=self.move_prof_down).pack(fill="x", pady=2)
        tk.Button(f_btns, text="👁 Toggle Visível", font=("Segoe UI", 8, "bold"), fg="#38bdf8", bg="#0c4a6e", bd=0, padx=12, pady=3, cursor="hand2", command=self.toggle_prof_enable).pack(fill="x", pady=(6, 2))
        tk.Button(f_btns, text="🌟 Alternar Pro (Argon)", font=("Segoe UI", 8, "bold"), fg="#e9d5ff", bg="#581c87", bd=0, padx=12, pady=3, cursor="hand2", command=self.toggle_prof_pro).pack(fill="x", pady=2)
        tk.Button(f_btns, text="✏️ Renomear Apelido", font=("Segoe UI", 8), fg="#e2e8f0", bg="#1e293b", bd=0, padx=12, pady=3, cursor="hand2", command=self.rename_profile_nickname).pack(fill="x", pady=2)
        tk.Button(f_btns, text="📂 Abrir Pasta", font=("Segoe UI", 8), fg="#e2e8f0", bg="#1e293b", bd=0, padx=12, pady=3, cursor="hand2", command=self.open_selected_profile_folder).pack(fill="x", pady=2)
        tk.Button(f_btns, text="➕ Novo Perfil...", font=("Segoe UI", 8, "bold"), fg="#a855f7", bg="#2e1065", bd=0, padx=12, pady=4, cursor="hand2", command=self.prompt_new_profile_dialog).pack(fill="x", pady=(8, 2))

        self.refresh_profile_listbox()
        sf.bind_mousewheel(f)

    def refresh_profile_listbox(self):
        self.prof_listbox.delete(0, tk.END)
        all_profiles = pm.discover_profiles()
        en_dict = self.config_copy.get("enabled_profiles", {})
        nicknames = self.config_copy.get("profile_nicknames", {})
        pro_dict = self.config_copy.get("pro_profiles", {"perfil4": True})

        for k in self.ordered_keys:
            is_en = en_dict.get(k, True)
            mark = "☑" if is_en else "☐"
            prof = all_profiles.get(k, {})
            disp = nicknames.get(k) or prof.get("display", k)
            cmd = get_profile_cli_command(k)
            info = pm.get_profile_info(prof)
            email = info.get("email", "Sem conta")
            is_pro = pro_dict.get(k, k == "perfil4")
            pro_badge = " [PRO / ARGON]" if is_pro else " [PADRÃO]"
            self.prof_listbox.insert(tk.END, f" {mark}  {disp}  [{cmd}]  —  {email}{pro_badge}")

    def toggle_prof_pro(self):
        sel = self.prof_listbox.curselection()
        if not sel:
            return
        k = self.ordered_keys[sel[0]]
        pro_dict = self.config_copy.setdefault("pro_profiles", {"perfil4": True})
        cur = pro_dict.get(k, k == "perfil4")
        pro_dict[k] = not cur
        self.refresh_profile_listbox()
        self.prof_listbox.selection_set(sel[0])

    def move_prof_up(self):
        sel = self.prof_listbox.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        self.ordered_keys[idx], self.ordered_keys[idx - 1] = self.ordered_keys[idx - 1], self.ordered_keys[idx]
        self.refresh_profile_listbox()
        self.prof_listbox.selection_set(idx - 1)

    def move_prof_down(self):
        sel = self.prof_listbox.curselection()
        if not sel or sel[0] >= len(self.ordered_keys) - 1:
            return
        idx = sel[0]
        self.ordered_keys[idx], self.ordered_keys[idx + 1] = self.ordered_keys[idx + 1], self.ordered_keys[idx]
        self.refresh_profile_listbox()
        self.prof_listbox.selection_set(idx + 1)

    def toggle_prof_enable(self):
        sel = self.prof_listbox.curselection()
        if not sel:
            return
        k = self.ordered_keys[sel[0]]
        en_dict = self.config_copy.setdefault("enabled_profiles", {})
        cur = en_dict.get(k, True)
        en_dict[k] = not cur
        self.refresh_profile_listbox()
        self.prof_listbox.selection_set(sel[0])

    def rename_profile_nickname(self):
        sel = self.prof_listbox.curselection()
        if not sel:
            return
        k = self.ordered_keys[sel[0]]
        nicknames = self.config_copy.setdefault("profile_nicknames", {})
        current_nick = nicknames.get(k, "")
        new_nick = simpledialog.askstring("Apelido do Perfil", f"Digite o apelido de exibição para {k}:", initialvalue=current_nick, parent=self)
        if new_nick is not None:
            if new_nick.strip():
                nicknames[k] = new_nick.strip()
            else:
                nicknames.pop(k, None)
            self.refresh_profile_listbox()
            self.prof_listbox.selection_set(sel[0])

    def open_selected_profile_folder(self):
        sel = self.prof_listbox.curselection()
        if not sel:
            return
        k = self.ordered_keys[sel[0]]
        all_profiles = pm.discover_profiles()
        prof = all_profiles.get(k)
        if prof and "root" in prof:
            open_folder(prof["root"])

    def prompt_new_profile_dialog(self):
        self.parent.prompt_new_profile()
        self.after(500, self.refresh_profile_listbox)

    # ---------------- TAB: COTAS & ALERTAS ----------------
    def build_tab_quotas(self):
        sf = ScrollableFrame(self.content_container, bg="#0f172a")
        self.tab_frames["quotas"] = sf
        f = sf.scrollable_window

        tk.Label(f, text="Monitoramento de Cotas & Alertas", font=("Segoe UI", 12, "bold"), fg="#f8fafc", bg="#0f172a").pack(anchor="w", pady=(0, 4))
        tk.Label(f, text="Entenda as cotas oficiais do Antigravity e configure limiares e tempos de telemetria.", font=("Segoe UI", 8), fg="#64748b", bg="#0f172a").pack(anchor="w", pady=(0, 10))

        # Antigravity Quotas Explanation Card
        card_info = tk.Frame(f, bg="#1e293b", bd=1, relief="solid", highlightbackground="#334155", highlightthickness=1)
        card_info.pack(fill="x", pady=(0, 12))

        tk.Label(card_info, text="📌 ESTRUTURA OFICIAL DE COTAS DO ANTIGRAVITY", font=("Segoe UI", 8, "bold"), fg="#38bdf8", bg="#1e293b").pack(anchor="w", padx=10, pady=(8, 4))
        
        rows_expl = [
            ("★ Cota Gemini", "Modelos: Gemini 3.8 Flash (Low, Medium, High)\nJanela móvel de 5 horas e limite semanal compartilhado."),
            ("⚡ Cota GPT/Claude", "Modelos: Claude Sonnet 4.6 (Thinking), Claude Opus 4.6 (Thinking), GPT-OSS 120B (Medium)\nCota única agrupada para modelos de terceiros."),
            ("✦ Cota Argon", "Modelos: Gemini 4 Argon (Low, Medium, High)\nExclusivo para assinantes de planos Pro pagos.")
        ]
        for title, desc in rows_expl:
            r = tk.Frame(card_info, bg="#1e293b")
            r.pack(fill="x", padx=10, pady=4)
            tk.Label(r, text=title, font=("Segoe UI", 8, "bold"), fg="#f8fafc", bg="#1e293b", width=18, anchor="w").pack(side="left", anchor="n")
            tk.Label(r, text=desc, font=("Segoe UI", 8), fg="#94a3b8", bg="#1e293b", justify="left", anchor="w").pack(side="left")

        # Refresh slider
        tk.Label(f, text="⏱ Ciclo de Atualização Automática:", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w", pady=(4, 2))
        f_ref = tk.Frame(f, bg="#0f172a")
        f_ref.pack(fill="x")

        self.ref_var = tk.IntVar(value=self.config_copy.get("refresh_seconds", 15))
        self.ref_lbl = tk.Label(f_ref, text=f"{self.ref_var.get()}s", font=("Segoe UI", 9, "bold"), fg="#22c55e", bg="#0f172a", width=5)
        self.ref_lbl.pack(side="right")

        scale_ref = tk.Scale(f_ref, from_=5, to=60, orient="horizontal", variable=self.ref_var, bg="#1e293b", fg="#f8fafc",
                             highlightthickness=0, bd=0, activebackground="#38bdf8", command=lambda v: self.ref_lbl.config(text=f"{v}s"))
        scale_ref.pack(fill="x", side="left", expand=True)

        # Alert Threshold
        tk.Label(f, text="🚨 Alerta de Cota Crítica:", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w", pady=(12, 2))
        f_alert = tk.Frame(f, bg="#0f172a")
        f_alert.pack(fill="x")

        self.thresh_var = tk.IntVar(value=self.config_copy.get("alert_threshold", 85))
        self.thresh_lbl = tk.Label(f_alert, text=f"{self.thresh_var.get()}%", font=("Segoe UI", 9, "bold"), fg="#ef4444", bg="#0f172a", width=5)
        self.thresh_lbl.pack(side="right")

        scale_thresh = tk.Scale(f_alert, from_=50, to=95, orient="horizontal", variable=self.thresh_var, bg="#1e293b", fg="#f8fafc",
                                highlightthickness=0, bd=0, activebackground="#ef4444", command=lambda v: self.thresh_lbl.config(text=f"{v}%"))
        scale_thresh.pack(fill="x", side="left", expand=True)

        # Bar options
        self.show_free_var = tk.BooleanVar(value=self.config_copy.get("show_free_pct", True))
        tk.Checkbutton(f, text="Exibir percentual livre (% restante) ao lado do percentual usado",
                       variable=self.show_free_var, font=("Segoe UI", 9), fg="#e2e8f0", bg="#0f172a",
                       selectcolor="#1e293b", activebackground="#0f172a", activeforeground="#e2e8f0").pack(anchor="w", pady=3)

        self.show_count_var = tk.BooleanVar(value=self.config_copy.get("show_countdown", True))
        tk.Checkbutton(f, text="Exibir tempo estimado para reset da cota (reset: Xh Ym)",
                       variable=self.show_count_var, font=("Segoe UI", 9), fg="#e2e8f0", bg="#0f172a",
                       selectcolor="#1e293b", activebackground="#0f172a", activeforeground="#e2e8f0").pack(anchor="w", pady=3)

        sf.bind_mousewheel(f)

    # ---------------- TAB: SISTEMA & WINDOWS ----------------
    def build_tab_system(self):
        sf = ScrollableFrame(self.content_container, bg="#0f172a")
        self.tab_frames["system"] = sf
        f = sf.scrollable_window

        tk.Label(f, text="Integração com o Windows & Sistema", font=("Segoe UI", 12, "bold"), fg="#f8fafc", bg="#0f172a").pack(anchor="w", pady=(0, 4))
        tk.Label(f, text="Configure inicialização automática, comportamento de janelas e manutenção.", font=("Segoe UI", 8), fg="#64748b", bg="#0f172a").pack(anchor="w", pady=(0, 14))

        # Windows Auto-start
        self.autostart_var = tk.BooleanVar(value=is_autostart_enabled())
        tk.Checkbutton(f, text="🚀 Iniciar com o Windows (ao ligar o computador)",
                       variable=self.autostart_var, font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a",
                       selectcolor="#1e293b", activebackground="#0f172a", activeforeground="#38bdf8").pack(anchor="w", pady=4)

        # Lock & Pin
        self.lock_var = tk.BooleanVar(value=self.config_copy.get("locked", False))
        tk.Checkbutton(f, text="🔒 Fixar posição do widget na tela (bloqueia arrastar)",
                       variable=self.lock_var, font=("Segoe UI", 9), fg="#e2e8f0", bg="#0f172a",
                       selectcolor="#1e293b", activebackground="#0f172a", activeforeground="#e2e8f0").pack(anchor="w", pady=4)

        self.pin_var = tk.BooleanVar(value=self.config_copy.get("always_on_top", True))
        tk.Checkbutton(f, text="📌 Sempre no Topo (Always on Top)",
                       variable=self.pin_var, font=("Segoe UI", 9), fg="#e2e8f0", bg="#0f172a",
                       selectcolor="#1e293b", activebackground="#0f172a", activeforeground="#e2e8f0").pack(anchor="w", pady=4)

        # Maintenance Buttons
        tk.Label(f, text="🛠️ Ações de Manutenção:", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w", pady=(16, 6))

        f_maint = tk.Frame(f, bg="#0f172a")
        f_maint.pack(fill="x")

        tk.Button(f_maint, text="🧹 Limpar Cache de Cotas", font=("Segoe UI", 8), fg="#cbd5e1", bg="#334155", bd=0, padx=10, pady=5, cursor="hand2", command=self.clear_cache).pack(side="left", padx=(0, 6))
        tk.Button(f_maint, text="📁 Abrir .antigravity-custom", font=("Segoe UI", 8), fg="#cbd5e1", bg="#334155", bd=0, padx=10, pady=5, cursor="hand2", command=lambda: open_folder(CUSTOM_DIR)).pack(side="left", padx=6)
        tk.Button(f_maint, text="🔄 Restaurar Padrões", font=("Segoe UI", 8), fg="#ef4444", bg="#450a0a", bd=0, padx=10, pady=5, cursor="hand2", command=self.restore_defaults).pack(side="left", padx=6)

        sf.bind_mousewheel(f)

    def clear_cache(self):
        cache_file = os.path.join(CUSTOM_DIR, "profiles_quotas.json")
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
            except Exception:
                pass
        self.parent.refresh_profiles(force=True)
        messagebox.showinfo("Cache Limpo", "O cache de cotas foi limpo com sucesso! Uma sincronização imediata foi iniciada.", parent=self)

    def restore_defaults(self):
        if messagebox.askyesno("Restaurar Padrões", "Deseja restaurar todas as configurações visuais para o padrão 2x2 Dark Slate?", parent=self):
            self.config_copy = DEFAULT_WIDGET_CONFIG.copy()
            self.parent.config_data = self.config_copy
            save_widget_config(self.config_copy)
            self.parent.apply_full_config()
            self.destroy()

    # ---------------- TAB: SOBRE & DIAGNÓSTICO ----------------
    def build_tab_about(self):
        sf = ScrollableFrame(self.content_container, bg="#0f172a")
        self.tab_frames["about"] = sf
        f = sf.scrollable_window

        tk.Label(f, text="Antigravity Quota Manager & Toolbar", font=("Segoe UI", 12, "bold"), fg="#f8fafc", bg="#0f172a").pack(anchor="w", pady=(0, 4))
        tk.Label(f, text="Versão 2.5.0 Pro — Monitoramento e Gestão Multi-Perfil para Google Antigravity", font=("Segoe UI", 8), fg="#64748b", bg="#0f172a").pack(anchor="w", pady=(0, 16))

        card = tk.Frame(f, bg="#1e293b", bd=1, relief="solid", highlightbackground="#334155", highlightthickness=1)
        card.pack(fill="x", pady=6, padx=2)

        active_key = pm.get_active_profile()
        all_profiles = pm.discover_profiles()
        active_info = pm.get_profile_info(all_profiles.get(active_key, {"name": active_key, "gemini_dir": ""})) if active_key in all_profiles else {}
        active_email = active_info.get("email", "Desconhecido")

        info_rows = [
            ("Usuário Windows:", os.environ.get("USERNAME", "ma038")),
            ("Perfil & Conta Ativa:", f"{active_key.upper()} — {active_email}"),
            ("Instância Única (Porta IPC):", f"127.0.0.1:{SINGLE_INSTANCE_PORT}"),
            ("Diretório de Configurações:", CUSTOM_DIR),
            ("Repositório de Código:", r"C:\55\3\agy-cli-toolbar"),
            ("Comandos CLI Suportados:", "agy (Perfil 1), agy2 (Perfil 2), agy3 (Perfil 3), agy4 (Perfil 4)..."),
            ("Cotas Suportadas:", "Gemini 3.8 Flash (5h/7d) • GPT/Claude (3P) • Gemini 4 Argon (Pro)")
        ]

        for label, val in info_rows:
            r = tk.Frame(card, bg="#1e293b")
            r.pack(fill="x", padx=10, pady=4)
            tk.Label(r, text=label, font=("Segoe UI", 8, "bold"), fg="#94a3b8", bg="#1e293b", width=26, anchor="w").pack(side="left")
            tk.Label(r, text=val, font=("Segoe UI", 8), fg="#f8fafc", bg="#1e293b", anchor="w").pack(side="left")

        f_log = tk.Frame(f, bg="#0f172a")
        f_log.pack(fill="x", pady=12)
        tk.Button(f_log, text="📄 Abrir Arquivo de Logs (tray.log)", font=("Segoe UI", 8), fg="#38bdf8", bg="#1e293b", bd=0, padx=12, pady=5, cursor="hand2", command=self.open_log_file).pack(side="left")

        sf.bind_mousewheel(f)

    def open_log_file(self):
        log_file = os.path.join(CUSTOM_DIR, "tray.log")
        if not os.path.exists(log_file):
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("Log do Antigravity Monitor iniciado.\n")
        open_folder(log_file)

    def save_and_apply(self):
        new_scale = round(self.zoom_var.get() / 100.0, 2)
        old_scale = float(self.config_copy.get("ui_scale", 1.20))
        self.config_copy["ui_scale"] = new_scale
        self.config_copy["font_size_offset"] = self.font_offset_var.get()

        preset = self.preset_var.get()
        if preset in GRID_PRESETS:
            cols, rows = GRID_PRESETS[preset]
            self.parent.cols = cols
            self.config_copy["grid_preset"] = preset
            self.config_copy["columns"] = cols

            # Calculate optimal window dimensions incorporating zoom scale
            card_h = 290 if self.default_expanded_var.get() else 225
            opt_w = min(max(int(round(cols * 350 * new_scale + 24)), 380), 2000)
            opt_h = min(max(int(round(rows * card_h * new_scale + 85)), 220), 1400)
            self.parent.geometry(f"{opt_w}x{opt_h}")
            self.config_copy["width"] = opt_w
            self.config_copy["height"] = opt_h
        elif new_scale != old_scale:
            ratio = new_scale / max(old_scale, 0.1)
            new_w = max(int(round(self.parent.winfo_width() * ratio)), 360)
            new_h = max(int(round(self.parent.winfo_height() * ratio)), 200)
            self.parent.geometry(f"{new_w}x{new_h}")
            self.config_copy["width"] = new_w
            self.config_copy["height"] = new_h

        self.config_copy["theme"] = self.theme_var.get()
        self.config_copy["refresh_seconds"] = self.ref_var.get()
        self.config_copy["opacity"] = self.op_var.get() / 100.0
        self.config_copy["privacy_mode"] = self.priv_var.get()
        self.config_copy["default_expanded"] = self.default_expanded_var.get()
        self.config_copy["card_density"] = self.density_var.get()
        self.config_copy["alert_threshold"] = self.thresh_var.get()
        self.config_copy["show_free_pct"] = self.show_free_var.get()
        self.config_copy["show_countdown"] = self.show_count_var.get()
        self.config_copy["locked"] = self.lock_var.get()
        self.config_copy["always_on_top"] = self.pin_var.get()
        self.config_copy["profile_order"] = self.ordered_keys

        # Apply Windows Autostart
        set_autostart(self.autostart_var.get())

        self.parent.config_data.update(self.config_copy)
        save_widget_config(self.parent.config_data)

        # Sync pro_profiles into profiles_quotas.json so CLI & Dashboard agree
        pro_dict = self.config_copy.get("pro_profiles", {})
        if pro_dict:
            q_file = os.path.join(CUSTOM_DIR, "profiles_quotas.json")
            try:
                q_data = {}
                if os.path.exists(q_file):
                    with open(q_file, "r", encoding="utf-8") as f:
                        q_data = json.load(f)
                for p_key, is_pro_val in pro_dict.items():
                    if p_key in q_data:
                        q_data[p_key]["is_pro"] = bool(is_pro_val)
                        if not is_pro_val:
                            q_data[p_key]["argon"] = None
                        elif not q_data[p_key].get("argon"):
                            q_data[p_key]["argon"] = {"used_pct": 0.0, "rem_pct": 100.0, "reset_in_seconds": 0}
                with open(q_file, "w", encoding="utf-8") as f:
                    json.dump(q_data, f, indent=2)
            except Exception:
                pass

        self.parent.apply_full_config()
        self.destroy()

class DesktopWidget(tk.Tk):
    def __init__(self, tray_controller=None):
        super().__init__()
        self.tray = tray_controller

        self.config_data = load_widget_config()
        self.cols = self.config_data.get("columns", 2)
        self.card_views = {}
        self.known_profiles_signature = ""
        self.expanded_cards = {}
        self.all_expanded = self.config_data.get("default_expanded", False)

        self.title("Antigravity Quotas")
        self.overrideredirect(True)
        self.attributes("-topmost", self.config_data.get("always_on_top", True))
        self.attributes("-alpha", self.config_data.get("opacity", 0.96))

        # Initial geometry
        x = self.config_data.get("x", 120)
        y = self.config_data.get("y", 80)
        w = self.config_data.get("width", 680)
        h = self.config_data.get("height", 370)
        # Ensure coordinates are within visible screen bounds
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        if x < 20 or x + 150 > screen_w:
            x = max((screen_w - w) // 2, 50)
        if y < 20 or y + 150 > screen_h:
            y = max((screen_h - h) // 2, 50)
        self.geometry(f"{w}x{h}+{x}+{y}")

        self.theme_colors = THEMES.get(self.config_data.get("theme", "Dark Slate"), THEMES["Dark Slate"])
        self.configure(bg=self.theme_colors["bg"])

        self._offset_x = 0
        self._offset_y = 0

        self.build_ui()
        self.bind_events()

        # Always make sure window is visible when launched
        self.config_data["visible"] = True
        save_widget_config(self.config_data)
        self.deiconify()
        self.lift()
        self.focus_force()

        self.refresh_profiles(force=True)
        self.schedule_next_refresh()

    def get_theme(self):
        return THEMES.get(self.config_data.get("theme", "Dark Slate"), THEMES["Dark Slate"])

    def get_font(self, base_size, weight="normal", family="Segoe UI"):
        scale = float(self.config_data.get("ui_scale", 1.20))
        offset = int(self.config_data.get("font_size_offset", 1))
        scaled_size = max(6, int(round((base_size + offset) * scale)))
        return (family, scaled_size, weight)

    def adjust_zoom(self, delta):
        cur_scale = float(self.config_data.get("ui_scale", 1.20))
        new_scale = round(max(0.70, min(cur_scale + delta, 2.50)), 2)
        if new_scale != cur_scale:
            self.set_zoom(new_scale)

    def set_zoom(self, scale_val):
        old_scale = float(self.config_data.get("ui_scale", 1.20))
        scale_val = round(max(0.70, min(scale_val, 2.50)), 2)
        self.config_data["ui_scale"] = scale_val

        # Scale window geometry proportionally
        ratio = scale_val / max(old_scale, 0.1)
        cur_w = self.winfo_width()
        cur_h = self.winfo_height()
        new_w = max(int(round(cur_w * ratio)), 360)
        new_h = max(int(round(cur_h * ratio)), 200)
        self.geometry(f"{new_w}x{new_h}")
        self.config_data["width"] = new_w
        self.config_data["height"] = new_h
        save_widget_config(self.config_data)

        if hasattr(self, "zoom_lbl"):
            self.zoom_lbl.config(text=f"{int(round(scale_val * 100))}%")

        self.apply_full_config()
        self.refresh_profiles(force=True)

    def set_font_offset(self, offset):
        self.config_data["font_size_offset"] = int(offset)
        save_widget_config(self.config_data)
        self.apply_full_config()
        self.refresh_profiles(force=True)

    def apply_full_config(self):
        self.theme_colors = self.get_theme()
        self.configure(bg=self.theme_colors["bg"])
        self.attributes("-alpha", self.config_data.get("opacity", 0.96))
        self.attributes("-topmost", self.config_data.get("always_on_top", True))

        # Update header & lock button state
        locked = self.config_data.get("locked", False)
        self.lock_btn.config(text="🔒 Fixado" if locked else "🔓 Mover", font=self.get_font(8, "bold"), fg=self.theme_colors["accent"] if locked else "#94a3b8")
        self.pin_btn.config(text="📌" if self.config_data.get("always_on_top", True) else "📍", font=self.get_font(9))
        self.grid_btn.config(text=f"⊞ {self.config_data.get('grid_preset', '2x2')}", font=self.get_font(8, "bold"))

        if hasattr(self, "zoom_lbl"):
            cur_pct = int(round(float(self.config_data.get("ui_scale", 1.20)) * 100))
            self.zoom_lbl.config(text=f"{cur_pct}%", font=self.get_font(8, "bold"))
        if hasattr(self, "btn_details"):
            self.btn_details.config(text="▲ Resumo" if self.all_expanded else "▼ Detalhes", font=self.get_font(8, "bold"), fg=self.theme_colors["accent"])
        if hasattr(self, "btn_settings"):
            self.btn_settings.config(font=self.get_font(8, "bold"))

        # Update styles of container
        self.outer_frame.config(bg=self.theme_colors["bg"], highlightbackground=self.theme_colors["card_border"])
        self.header.config(bg=self.theme_colors["header_bg"])
        self.title_lbl.config(bg=self.theme_colors["header_bg"], fg=self.theme_colors["text"], font=self.get_font(10, "bold"))
        if hasattr(self, "kpi_bar"):
            self.kpi_bar.config(bg=self.theme_colors["footer_bg"], highlightbackground=self.theme_colors["card_border"])
            self.kpi_active_lbl.config(bg=self.theme_colors["footer_bg"], font=self.get_font(8, "bold"))
            self.kpi_best_lbl.config(bg=self.theme_colors["footer_bg"], font=self.get_font(8, "bold"))
            self.kpi_stats_lbl.config(bg=self.theme_colors["footer_bg"], fg=self.theme_colors["text_muted"], font=self.get_font(8))
        self.grid_container.config(bg=self.theme_colors["bg"])
        self.footer.config(bg=self.theme_colors["footer_bg"])
        self.time_lbl.config(bg=self.theme_colors["footer_bg"], font=self.get_font(8))
        if hasattr(self, "btn_refresh"):
            self.btn_refresh.config(font=self.get_font(8, "bold"))
        if hasattr(self, "btn_new"):
            self.btn_new.config(font=self.get_font(8, "bold"))

        self.refresh_profiles(force=True)

    def bring_to_front(self):
        """Wakes up the widget cleanly without creating duplicates and forces it into foreground."""
        try:
            self.deiconify()
            self.overrideredirect(True)
            self.attributes("-topmost", True)
            self.lift()
            self.focus_force()
            self.config_data["visible"] = True
            save_widget_config(self.config_data)
            self.refresh_profiles(force=True)

            # Win32 forceful foreground pop
            try:
                import ctypes
                user32 = ctypes.windll.user32
                hwnd = user32.GetParent(self.winfo_id()) or self.winfo_id()
                user32.ShowWindow(hwnd, 9)  # SW_RESTORE
                user32.ShowWindow(hwnd, 5)  # SW_SHOW
                fore_hwnd = user32.GetForegroundWindow()
                fore_tid = user32.GetWindowThreadProcessId(fore_hwnd, None)
                cur_tid = ctypes.windll.kernel32.GetCurrentThreadId()
                if fore_tid != cur_tid:
                    user32.AttachThreadInput(fore_tid, cur_tid, True)
                    user32.SetForegroundWindow(hwnd)
                    user32.BringWindowToTop(hwnd)
                    user32.AttachThreadInput(fore_tid, cur_tid, False)
                else:
                    user32.SetForegroundWindow(hwnd)
                    user32.BringWindowToTop(hwnd)
                user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0040)
            except Exception:
                pass

            self._ensure_taskbar_presence()

            # If user didn't pin always_on_top, keep it topmost for 4 seconds so they clearly see it pop up
            if not self.config_data.get("always_on_top", True):
                self.after(4000, lambda: self.attributes("-topmost", False))
        except Exception:
            pass

    def _ensure_taskbar_presence(self):
        try:
            import ctypes
            GWL_EXSTYLE = -20
            WS_EX_APPWINDOW = 0x00040000
            WS_EX_TOOLWINDOW = 0x00000080
            hwnd = ctypes.windll.user32.GetParent(self.winfo_id()) or self.winfo_id()
            style = ctypes.windll.user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
            style = (style | WS_EX_APPWINDOW) & ~WS_EX_TOOLWINDOW
            ctypes.windll.user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style)
        except Exception:
            pass

    def build_ui(self):
        self.outer_frame = tk.Frame(self, bg=self.theme_colors["bg"], bd=1, relief="solid",
                                    highlightbackground=self.theme_colors["card_border"], highlightthickness=1)
        self.outer_frame.pack(fill="both", expand=True)

        self.after(100, self._ensure_taskbar_presence)

        # Header Bar
        self.header = tk.Frame(self.outer_frame, bg=self.theme_colors["header_bg"], height=38)
        self.header.pack(fill="x", side="top")

        self.title_lbl = tk.Label(self.header, text="⚡ Antigravity Monitor", font=self.get_font(10, "bold"),
                                  fg=self.theme_colors["text"], bg=self.theme_colors["header_bg"])
        self.title_lbl.pack(side="left", padx=10, pady=6)

        # Header Action Buttons
        btn_close = tk.Label(self.header, text="✕", font=self.get_font(10, "bold"), fg="#94a3b8", bg=self.theme_colors["header_bg"], cursor="hand2")
        btn_close.pack(side="right", padx=(4, 10))
        btn_close.bind("<Button-1>", lambda e: self.hide_widget())

        self.pin_btn = tk.Label(self.header, text="📌" if self.config_data.get("always_on_top", True) else "📍",
                                font=self.get_font(9), fg="#94a3b8", bg=self.theme_colors["header_bg"], cursor="hand2")
        self.pin_btn.pack(side="right", padx=4)
        self.pin_btn.bind("<Button-1>", lambda e: self.toggle_pin())

        locked = self.config_data.get("locked", False)
        self.lock_btn = tk.Label(self.header, text="🔒 Fixado" if locked else "🔓 Mover", font=self.get_font(8, "bold"),
                                 fg=self.theme_colors["accent"] if locked else "#94a3b8", bg=self.theme_colors["header_bg"], cursor="hand2")
        self.lock_btn.pack(side="right", padx=4)
        self.lock_btn.bind("<Button-1>", lambda e: self.toggle_lock())

        self.grid_btn = tk.Label(self.header, text=f"⊞ {self.config_data.get('grid_preset', '2x2')}", font=self.get_font(8, "bold"),
                                 fg=self.theme_colors["accent"], bg=self.theme_colors["header_bg"], cursor="hand2")
        self.grid_btn.pack(side="right", padx=4)
        self.grid_btn.bind("<Button-1>", lambda e: self.quick_cycle_grid())

        # Quick Zoom Controls in Header: [-] 120% [+]
        self.zoom_frame = tk.Frame(self.header, bg=self.theme_colors["header_bg"])
        self.zoom_frame.pack(side="right", padx=3)

        btn_zoom_out = tk.Label(self.zoom_frame, text="🔍-", font=self.get_font(8, "bold"),
                                fg="#94a3b8", bg=self.theme_colors["header_bg"], cursor="hand2")
        btn_zoom_out.pack(side="left", padx=1)
        btn_zoom_out.bind("<Button-1>", lambda e: self.adjust_zoom(-0.10))

        cur_pct = int(round(float(self.config_data.get("ui_scale", 1.20)) * 100))
        self.zoom_lbl = tk.Label(self.zoom_frame, text=f"{cur_pct}%", font=self.get_font(8, "bold"),
                                 fg=self.theme_colors["accent"], bg=self.theme_colors["header_bg"], cursor="hand2")
        self.zoom_lbl.pack(side="left", padx=2)
        self.zoom_lbl.bind("<Button-1>", lambda e: self.set_zoom(1.0))

        btn_zoom_in = tk.Label(self.zoom_frame, text="+", font=self.get_font(8, "bold"),
                               fg="#94a3b8", bg=self.theme_colors["header_bg"], cursor="hand2")
        btn_zoom_in.pack(side="left", padx=1)
        btn_zoom_in.bind("<Button-1>", lambda e: self.adjust_zoom(0.10))

        self.btn_details = tk.Label(self.header, text="▲ Resumo" if self.all_expanded else "▼ Detalhes",
                                    font=self.get_font(8, "bold"), fg=self.theme_colors["accent"],
                                    bg=self.theme_colors["header_bg"], cursor="hand2")
        self.btn_details.pack(side="right", padx=4)
        self.btn_details.bind("<Button-1>", lambda e: self.toggle_all_cards_detail())
        ToolTip(self.btn_details, "Alternar entre modo resumido e detalhado em todos os perfis")

        self.btn_settings = tk.Label(self.header, text="⚙️ Ajustes", font=self.get_font(8, "bold"), fg="#38bdf8",
                                     bg=self.theme_colors["header_bg"], cursor="hand2")
        self.btn_settings.pack(side="right", padx=4)
        self.btn_settings.bind("<Button-1>", lambda e: self.open_settings())

        # Executive Summary KPI Strip
        self.kpi_bar = tk.Frame(self.outer_frame, bg=self.theme_colors["footer_bg"], bd=0,
                                highlightbackground=self.theme_colors["card_border"], highlightthickness=1)
        self.kpi_bar.pack(fill="x", side="top", padx=8, pady=(4, 0))

        self.kpi_active_lbl = tk.Label(self.kpi_bar, text="🟢 Ativo: --", font=self.get_font(8, "bold"),
                                       fg="#22c55e", bg=self.theme_colors["footer_bg"])
        self.kpi_active_lbl.pack(side="left", padx=(8, 12), pady=3)

        self.kpi_best_lbl = tk.Label(self.kpi_bar, text="💡 Melhor Livre: --", font=self.get_font(8, "bold"),
                                     fg="#38bdf8", bg=self.theme_colors["footer_bg"], cursor="hand2")
        self.kpi_best_lbl.pack(side="left", padx=(0, 10), pady=3)
        self.best_free_profile_key = None
        self.kpi_best_lbl.bind("<Button-1>", lambda e: self.activate_best_free_profile())
        ToolTip(self.kpi_best_lbl, "Clique para ativar o perfil com maior cota livre disponível")

        self.kpi_stats_lbl = tk.Label(self.kpi_bar, text="Contas: --", font=self.get_font(8),
                                      fg=self.theme_colors["text_muted"], bg=self.theme_colors["footer_bg"])
        self.kpi_stats_lbl.pack(side="right", padx=8, pady=3)

        # Grid Profiles Container
        self.grid_container = tk.Frame(self.outer_frame, bg=self.theme_colors["bg"])
        self.grid_container.pack(fill="both", expand=True, padx=8, pady=6)

        # Footer Bar
        self.footer = tk.Frame(self.outer_frame, bg=self.theme_colors["footer_bg"], height=30)
        self.footer.pack(fill="x", side="bottom")

        self.time_lbl = tk.Label(self.footer, text="Atualizado", font=self.get_font(8), fg="#64748b", bg=self.theme_colors["footer_bg"])
        self.time_lbl.pack(side="left", padx=8)

        self.resize_grip = ResizeGrip(self.footer, self)
        self.resize_grip.pack(side="right", padx=(2, 0))

        self.btn_refresh = tk.Label(self.footer, text="🔄 Atualizar", font=self.get_font(8, "bold"), fg="#38bdf8",
                                    bg=self.theme_colors["footer_bg"], cursor="hand2")
        self.btn_refresh.pack(side="right", padx=6)
        self.btn_refresh.bind("<Button-1>", lambda e: self.refresh_profiles(force=True))

        self.btn_new = tk.Label(self.footer, text="➕ Novo Perfil", font=self.get_font(8, "bold"), fg="#a855f7",
                                bg=self.theme_colors["footer_bg"], cursor="hand2")
        self.btn_new.pack(side="right", padx=6)
        self.btn_new.bind("<Button-1>", lambda e: self.prompt_new_profile())

    def bind_events(self):
        for widget in [self.header, self.outer_frame, self.title_lbl]:
            widget.bind("<ButtonPress-1>", self.on_drag_start)
            widget.bind("<B1-Motion>", self.on_drag_motion)
            widget.bind("<ButtonRelease-1>", self.on_drag_end)

        # Mouse Wheel & Shortcut Zoom
        self.bind("<Control-MouseWheel>", lambda e: self.adjust_zoom(0.10 if e.delta > 0 else -0.10))
        self.bind("<Control-plus>", lambda e: self.adjust_zoom(0.10))
        self.bind("<Control-equal>", lambda e: self.adjust_zoom(0.10))
        self.bind("<Control-minus>", lambda e: self.adjust_zoom(-0.10))
        self.bind("<Control-0>", lambda e: self.set_zoom(1.0))

    def on_drag_start(self, event):
        if not self.config_data.get("locked", False):
            self._offset_x = event.x
            self._offset_y = event.y

    def on_drag_motion(self, event):
        if not self.config_data.get("locked", False):
            x = self.winfo_x() + (event.x - self._offset_x)
            y = self.winfo_y() + (event.y - self._offset_y)
            self.geometry(f"+{x}+{y}")

    def on_drag_end(self, event):
        if not self.config_data.get("locked", False):
            self.config_data["x"] = self.winfo_x()
            self.config_data["y"] = self.winfo_y()
            save_widget_config(self.config_data)

    def toggle_lock(self):
        new_val = not self.config_data.get("locked", False)
        self.config_data["locked"] = new_val
        self.lock_btn.config(text="🔒 Fixado" if new_val else "🔓 Mover", fg=self.theme_colors["accent"] if new_val else "#94a3b8")
        save_widget_config(self.config_data)

    def toggle_pin(self):
        new_val = not self.config_data.get("always_on_top", True)
        self.config_data["always_on_top"] = new_val
        self.attributes("-topmost", new_val)
        self.pin_btn.config(text="📌" if new_val else "📍")
        save_widget_config(self.config_data)

    def open_settings(self):
        SettingsDialog(self)

    def quick_cycle_grid(self):
        cycle = ["2x2", "1x4", "4x1", "1x2", "2x1", "2x3", "3x2"]
        cur = self.config_data.get("grid_preset", "2x2")
        next_idx = (cycle.index(cur) + 1) % len(cycle) if cur in cycle else 0
        new_preset = cycle[next_idx]

        cols, rows = GRID_PRESETS[new_preset]
        self.cols = cols
        self.config_data["grid_preset"] = new_preset
        self.config_data["columns"] = cols

        scale = float(self.config_data.get("ui_scale", 1.20))
        card_h = 290 if getattr(self, "all_expanded", False) else 225
        opt_w = min(max(int(round(cols * 350 * scale + 24)), 380), 2000)
        opt_h = min(max(int(round(rows * card_h * scale + 85)), 220), 1400)
        self.geometry(f"{opt_w}x{opt_h}")
        self.config_data["width"] = opt_w
        self.config_data["height"] = opt_h
        save_widget_config(self.config_data)

        self.grid_btn.config(text=f"⊞ {new_preset}")
        self.refresh_profiles(force=True)

    def hide_widget(self):
        self.withdraw()
        self.config_data["visible"] = False
        save_widget_config(self.config_data)

    def show_widget(self):
        self.deiconify()
        self.lift()
        self.config_data["visible"] = True
        save_widget_config(self.config_data)
        self.refresh_profiles(force=True)

    def toggle_visibility(self):
        if self.winfo_viewable():
            self.hide_widget()
        else:
            self.show_widget()

    def create_compact_bargraph(self, parent, height=None):
        scale = float(self.config_data.get("ui_scale", 1.20))
        offset = int(self.config_data.get("font_size_offset", 1))
        if height is None:
            height = max(18, int(round((18 + offset * 1.5) * scale)))
        bar_font = self.get_font(8, "bold")
        cv = tk.Canvas(parent, height=height, bg=self.theme_colors["bar_bg"], bd=0, highlightthickness=0)
        track_id = cv.create_rectangle(0, 0, 10, height, fill=self.theme_colors["bar_bg"], width=0)
        fill_id = cv.create_rectangle(0, 0, 0, height, fill="#22c55e", width=0)
        left_id = cv.create_text(8, height // 2, text="", anchor="w", fill="#ffffff", font=bar_font)
        right_id = cv.create_text(10, height // 2, text="", anchor="e", fill="#ffffff", font=bar_font)
        bar_data = {
            "cv": cv,
            "track_id": track_id,
            "fill_id": fill_id,
            "left_id": left_id,
            "right_id": right_id,
            "height": height,
            "pct": 0.0,
            "left_text": "",
            "right_text": "",
            "fill_col": "#22c55e"
        }
        cv.bind("<Configure>", lambda e, d=bar_data: self.on_bar_configure(e, d))
        return bar_data

    def on_bar_configure(self, event, d):
        w = event.width
        if w < 10:
            return
        h = d["height"]
        fill_w = int((d["pct"] / 100.0) * w)
        d["cv"].coords(d["track_id"], 0, 0, w, h)
        d["cv"].coords(d["fill_id"], 0, 0, fill_w, h)
        d["cv"].coords(d["left_id"], 8, h // 2)
        d["cv"].coords(d["right_id"], w - 8, h // 2)

    def update_compact_bargraph(self, d, pct, left_text, right_text, theme_color=None, track_color=None):
        pct = min(max(pct, 0.0), 100.0)
        d["pct"] = pct
        d["left_text"] = left_text
        d["right_text"] = right_text

        thresh = self.config_data.get("alert_threshold", 85)
        if pct >= thresh:
            col = "#ef4444"
        elif pct >= 60:
            col = "#eab308"
        elif theme_color:
            col = theme_color
        else:
            col = "#22c55e"
        d["fill_col"] = col

        track_bg = track_color if track_color else self.theme_colors["bar_bg"]

        w = d["cv"].winfo_width()
        if w < 50:
            w = 260
        h = d["height"]
        fill_w = int((pct / 100.0) * w)

        bar_font = self.get_font(8, "bold")
        d["cv"].coords(d["track_id"], 0, 0, w, h)
        d["cv"].itemconfig(d["track_id"], fill=track_bg)
        d["cv"].coords(d["fill_id"], 0, 0, fill_w, h)
        d["cv"].itemconfig(d["fill_id"], fill=col)

        d["cv"].coords(d["left_id"], 8, h // 2)
        d["cv"].itemconfig(d["left_id"], text=left_text, font=bar_font)

        d["cv"].coords(d["right_id"], w - 8, h // 2)
        d["cv"].itemconfig(d["right_id"], text=right_text, font=bar_font)

    def toggle_card_detail(self, profile_key):
        is_exp = self.expanded_cards.get(profile_key, self.all_expanded)
        self.expanded_cards[profile_key] = not is_exp
        self.refresh_profiles()

    def toggle_all_cards_detail(self):
        self.all_expanded = not self.all_expanded
        for k in self.card_views.keys():
            self.expanded_cards[k] = self.all_expanded
        if hasattr(self, "btn_details"):
            self.btn_details.config(text="▲ Resumo" if self.all_expanded else "▼ Detalhes")
        self.refresh_profiles()

    def activate_best_free_profile(self):
        if getattr(self, "best_free_profile_key", None):
            self.switch_profile_and_refresh(self.best_free_profile_key)

    def show_profile_context_menu(self, event, profile_key):
        profiles = pm.discover_profiles()
        prof = profiles.get(profile_key, {})
        info = pm.get_profile_info(prof) if prof else {}
        cmd_name = get_profile_cli_command(profile_key)
        is_exp = self.expanded_cards.get(profile_key, self.all_expanded)
        is_pro = info.get("is_pro", False)

        menu = tk.Menu(self, tearoff=0, bg="#1e293b", fg="#f8fafc",
                       activebackground="#0284c7", activeforeground="#ffffff",
                       font=("Segoe UI", 9))
        menu.add_command(label=f"⚡ Abrir CLI ({cmd_name})", command=lambda: open_cmd_for_profile(profile_key))
        menu.add_command(label="🖥️ Abrir Desktop", command=lambda: pm.cmd_desktop(profile_key))
        menu.add_command(label="🔄 Ativar Perfil", command=lambda: self.switch_profile_and_refresh(profile_key))
        menu.add_separator()
        menu.add_command(
            label="▲ Recolher Modelos" if is_exp else "▼ Detalhar Modelos",
            command=lambda: self.toggle_card_detail(profile_key)
        )
        menu.add_command(label="✏️ Renomear Apelido...", command=lambda: self.rename_profile_inline(profile_key))
        menu.add_command(
            label="✦ Desativar Argon (Padrão)" if is_pro else "✦ Ativar Plano Pro (Argon)",
            command=lambda: self.toggle_profile_pro_inline(profile_key)
        )
        menu.add_separator()
        if prof.get("root"):
            menu.add_command(label="📁 Abrir Pasta do Perfil", command=lambda: open_folder(prof["root"]))
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def rename_profile_inline(self, profile_key):
        nicknames = self.config_data.setdefault("profile_nicknames", {})
        cur = nicknames.get(profile_key, "")
        new_nick = simpledialog.askstring(
            "Renomear Perfil",
            f"Digite o apelido para {profile_key} (vazio para padrão):",
            initialvalue=cur,
            parent=self
        )
        if new_nick is not None:
            if new_nick.strip():
                nicknames[profile_key] = new_nick.strip()
            else:
                nicknames.pop(profile_key, None)
            save_widget_config(self.config_data)
            self.refresh_profiles(force=True)

    def toggle_profile_pro_inline(self, profile_key):
        pro_dict = self.config_data.setdefault("pro_profiles", {"perfil4": True})
        cur = pro_dict.get(profile_key, profile_key == "perfil4")
        new_val = not cur
        pro_dict[profile_key] = new_val
        save_widget_config(self.config_data)

        q_file = os.path.join(CUSTOM_DIR, "profiles_quotas.json")
        try:
            q_data = {}
            if os.path.exists(q_file):
                with open(q_file, "r", encoding="utf-8") as f:
                    q_data = json.load(f)
            if profile_key in q_data:
                q_data[profile_key]["is_pro"] = new_val
                if not new_val:
                    q_data[profile_key]["argon"] = None
                elif not q_data[profile_key].get("argon"):
                    q_data[profile_key]["argon"] = {"used_pct": 0.0, "rem_pct": 100.0, "reset_in_seconds": 0}
                with open(q_file, "w", encoding="utf-8") as f:
                    json.dump(q_data, f, indent=2)
        except Exception:
            pass
        self.refresh_profiles(force=True)

    def build_profile_card(self, parent, key, prof, row, col):
        is_active = (key == pm.get_active_profile())
        th = self.theme_colors
        card_bg = th["card_active_bg"] if is_active else th["card_bg"]
        border_col = th["card_active_border"] if is_active else th["card_border"]
        border_w = 2 if is_active else 1

        card = tk.Frame(parent, bg=card_bg, bd=1, relief="solid", highlightbackground=border_col, highlightthickness=border_w)
        card.grid(row=row, column=col, padx=4, pady=4, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)

        # Row 1: Header Row (Dot + Name + Command + ATIVO Tag + Status + Detalhes + Arrows + Context Menu)
        row_top = tk.Frame(card, bg=card_bg)
        row_top.pack(fill="x", padx=8, pady=(4, 1))

        dot_lbl = tk.Label(row_top, text="●", font=self.get_font(9), fg="#22c55e" if is_active else "#64748b", bg=card_bg)
        dot_lbl.pack(side="left", padx=(0, 4))

        cmd_name = get_profile_cli_command(key)
        nicknames = self.config_data.get("profile_nicknames", {})
        display_name = nicknames.get(key) or prof.get("display", key.upper())

        name_lbl = tk.Label(row_top, text=f"{display_name} ({cmd_name})", font=self.get_font(9, "bold"),
                            fg=th["accent"] if is_active else th["text"], bg=card_bg)
        name_lbl.pack(side="left")

        tag_lbl = tk.Label(row_top, text="ATIVO", font=self.get_font(7, "bold"), fg=th["tag_fg"], bg=th["tag_bg"], padx=3, pady=0)
        if is_active:
            tag_lbl.pack(side="left", padx=4)

        # Right box: Status, Detalhes, Reorder arrows, and Menu button
        top_right = tk.Frame(row_top, bg=card_bg)
        top_right.pack(side="right")

        status_lbl = tk.Label(top_right, text="", font=self.get_font(8, "bold"), fg="#22c55e", bg=card_bg)
        status_lbl.pack(side="left", padx=(0, 4))

        is_expanded = self.expanded_cards.get(key, self.all_expanded)
        btn_detail = tk.Label(top_right, text="▲ Resumo" if is_expanded else "▼ Detalhes",
                              font=self.get_font(7, "bold"), fg="#38bdf8", bg=card_bg, cursor="hand2")
        btn_detail.pack(side="left", padx=(0, 4))
        btn_detail.bind("<Button-1>", lambda e, p=key: self.toggle_card_detail(p))
        ToolTip(btn_detail, "Clique para expandir ou recolher os modelos exatos de cada cota")

        btn_left = tk.Label(top_right, text="◀", font=self.get_font(9), fg="#64748b", bg=card_bg, cursor="hand2")
        btn_left.pack(side="left", padx=1)
        btn_left.bind("<Button-1>", lambda e, p=key: self.shift_profile_order(p, -1))

        btn_right = tk.Label(top_right, text="▶", font=self.get_font(9), fg="#64748b", bg=card_bg, cursor="hand2")
        btn_right.pack(side="left", padx=1)
        btn_right.bind("<Button-1>", lambda e, p=key: self.shift_profile_order(p, 1))

        btn_menu = tk.Label(top_right, text="⋮", font=self.get_font(9, "bold"), fg="#94a3b8", bg=card_bg, cursor="hand2")
        btn_menu.pack(side="left", padx=(3, 0))
        btn_menu.bind("<Button-1>", lambda e, p=key: self.show_profile_context_menu(e, p))
        ToolTip(btn_menu, "Ações rápidas do perfil (ou clique direito no cartão)")

        # Row 2: Email & Badges Row
        row_meta = tk.Frame(card, bg=card_bg)
        row_meta.pack(fill="x", padx=8, pady=(0, 2))

        email_lbl = tk.Label(row_meta, text="Carregando...", font=self.get_font(8), fg=th["text_muted"], bg=card_bg)
        email_lbl.pack(side="left")

        badges_box = tk.Frame(row_meta, bg=card_bg)
        badges_box.pack(side="right")

        # Row 3: Bars Container (In-bar bargraphs for Gemini 5h, Gemini 7d, GPT/Claude 3P, and Argon if Pro)
        bars_container = tk.Frame(card, bg=card_bg)
        bars_container.pack(fill="x", padx=8, pady=(2, 2))

        if not hasattr(self, "bar_tooltips"):
            self.bar_tooltips = {}

        # 1. Gemini (5h) in-bar
        gem5_row = tk.Frame(bars_container, bg=card_bg)
        gem5_row.pack(fill="x", pady=1)
        gem5_bar = self.create_compact_bargraph(gem5_row)
        gem5_bar["cv"].pack(fill="x", expand=True)
        tt_gem5 = ToolTip(gem5_bar["cv"], "★ COTA GEMINI (5h)")

        # 2. Gemini (7d) in-bar
        gemw_row = tk.Frame(bars_container, bg=card_bg)
        gemw_row.pack(fill="x", pady=1)
        gemw_bar = self.create_compact_bargraph(gemw_row)
        gemw_bar["cv"].pack(fill="x", expand=True)
        tt_gemw = ToolTip(gemw_bar["cv"], "📅 COTA GEMINI SEMANAL (7d)")

        # 3. Outros (GPT / Claude) in-bar
        outros_row = tk.Frame(bars_container, bg=card_bg)
        outros_row.pack(fill="x", pady=1)
        outros_bar = self.create_compact_bargraph(outros_row)
        outros_bar["cv"].pack(fill="x", expand=True)
        tt_outros = ToolTip(outros_bar["cv"], "⚡ COTA GPT / CLAUDE (Outros)")

        # 4. Argon (Pro) in-bar - Empacotado apenas em perfis com plano Pro
        argon_row = tk.Frame(bars_container, bg=card_bg)
        argon_bar = self.create_compact_bargraph(argon_row)
        argon_bar["cv"].pack(fill="x", expand=True)
        tt_argon = ToolTip(argon_bar["cv"], "✦ COTA ARGON (Plano Pro Pago)")
        if not hasattr(self, "argon_tooltips"):
            self.argon_tooltips = {}
        self.argon_tooltips[key] = tt_argon
        self.bar_tooltips[key] = {
            "gem5": tt_gem5,
            "gemw": tt_gemw,
            "outros": tt_outros,
            "argon": tt_argon,
        }

        # Row 4: Expandable Drawer (Lista explicativa com os modelos exatos de cada cota)
        drawer = tk.Frame(card, bg=self.theme_colors.get("header_bg", "#0f172a"), bd=1, relief="solid",
                          highlightbackground=border_col, highlightthickness=1)

        # Seção Gemini no Drawer
        f_gem_det = tk.Frame(drawer, bg=drawer["bg"])
        f_gem_det.pack(fill="x", padx=6, pady=2)
        tk.Label(f_gem_det, text="★ Gemini:", font=self.get_font(7, "bold"), fg="#38bdf8", bg=drawer["bg"]).pack(side="left")
        tk.Label(f_gem_det, text="Gemini 3.8 Flash (Low • Medium • High)", font=self.get_font(7), fg="#cbd5e1", bg=drawer["bg"]).pack(side="left", padx=4)

        # Seção Outros (GPT / Claude) no Drawer
        f_out_det = tk.Frame(drawer, bg=drawer["bg"])
        f_out_det.pack(fill="x", padx=6, pady=2)
        tk.Label(f_out_det, text="⚡ GPT/Claude:", font=self.get_font(7, "bold"), fg="#34d399", bg=drawer["bg"]).pack(side="left")
        tk.Label(f_out_det, text="Claude Sonnet 4.6 • Claude Opus 4.6 • GPT-OSS 120B", font=self.get_font(7), fg="#cbd5e1", bg=drawer["bg"]).pack(side="left", padx=4)

        # Seção Argon no Drawer - Empacotada apenas se is_pro for True
        f_arg_det = tk.Frame(drawer, bg=drawer["bg"])
        lbl_arg_title = tk.Label(f_arg_det, text="✦ Argon (Pro):", font=self.get_font(7, "bold"), fg="#c084fc", bg=drawer["bg"])
        lbl_arg_title.pack(side="left")
        lbl_arg_models = tk.Label(f_arg_det, text="Gemini 4 Argon (Low • Medium • High)", font=self.get_font(7), fg="#cbd5e1", bg=drawer["bg"])
        lbl_arg_models.pack(side="left", padx=4)

        if is_expanded:
            drawer.pack(fill="x", padx=8, pady=(2, 4))

        # Row 5: Action Buttons Row (Ultra-compact, ancorado na base para alinhamento perfeito)
        btn_box = tk.Frame(card, bg=card_bg)
        btn_box.pack(fill="x", side="bottom", padx=8, pady=(2, 4))

        btn_cmd = tk.Button(btn_box, text=f"⚡ CLI ({cmd_name})", font=self.get_font(8, "bold"), fg="#ffffff", bg="#0284c7",
                            activebackground="#0369a1", activeforeground="#ffffff", bd=0, padx=6, pady=2, cursor="hand2",
                            command=lambda p=key: open_cmd_for_profile(p))
        btn_cmd.pack(side="left")

        btn_desktop = tk.Button(btn_box, text="🖥️ Desktop", font=self.get_font(8), fg="#cbd5e1", bg="#334155",
                                activebackground="#475569", activeforeground="#ffffff", bd=0, padx=5, pady=2, cursor="hand2",
                                command=lambda p=key: pm.cmd_desktop(p))
        btn_desktop.pack(side="left", padx=3)

        btn_activate = tk.Button(btn_box, text="Ativar", font=self.get_font(8, "bold"), fg="#a855f7", bg="#2e1065",
                                 activebackground="#3b0764", activeforeground="#ffffff", bd=0, padx=6, pady=2, cursor="hand2",
                                 command=lambda p=key: self.switch_profile_and_refresh(p))
        btn_activate.pack(side="right")

        card.bind("<Double-Button-1>", lambda e, p=key: open_cmd_for_profile(p))
        card.bind("<Button-3>", lambda e, p=key: self.show_profile_context_menu(e, p))

        self.card_views[key] = {
            "card": card,
            "dot_lbl": dot_lbl,
            "name_lbl": name_lbl,
            "tag_lbl": tag_lbl,
            "email_lbl": email_lbl,
            "status_lbl": status_lbl,
            "btn_detail": btn_detail,
            "badges_box": badges_box,
            "gem5_bar": gem5_bar,
            "gemw_bar": gemw_bar,
            "outros_bar": outros_bar,
            "argon_row": argon_row,
            "argon_bar": argon_bar,
            "drawer": drawer,
            "f_arg_det": f_arg_det,
            "lbl_arg_title": lbl_arg_title,
            "lbl_arg_models": lbl_arg_models,
            "btn_activate": btn_activate
        }

    def shift_profile_order(self, profile_key, direction):
        order = self.config_data.get("profile_order", [])
        if profile_key not in order:
            return
        idx = order.index(profile_key)
        new_idx = idx + direction
        if 0 <= new_idx < len(order):
            order[idx], order[new_idx] = order[new_idx], order[idx]
            self.config_data["profile_order"] = order
            save_widget_config(self.config_data)
            self.refresh_profiles(force=True)

    def update_card_in_place(self, key, prof, info, is_active):
        if key not in self.card_views:
            return

        view = self.card_views[key]
        th = self.theme_colors
        card_bg = th["card_active_bg"] if is_active else th["card_bg"]
        border_col = th["card_active_border"] if is_active else th["card_border"]
        border_w = 2 if is_active else 1

        # Alert highlight if critical
        thresh = self.config_data.get("alert_threshold", 85)
        g5 = info.get("gemini_5h") or info.get("quota_5h") or {}
        gw = info.get("gemini_7d") or info.get("quota_weekly") or {}
        ot = info.get("outros_3p") or {}
        ar = info.get("argon") or {}

        used_5h = float(g5.get("used_pct", 0.0))
        used_w = float(gw.get("used_pct", 0.0))
        used_ot = float(ot.get("used_pct", 0.0))
        used_ar = float(ar.get("used_pct", 0.0)) if info.get("is_pro") else 0.0

        if max(used_5h, used_w, used_ot, used_ar) >= thresh:
            border_col = "#ef4444"

        view["card"].config(bg=card_bg, highlightbackground=border_col, highlightthickness=border_w)
        view["dot_lbl"].config(fg="#22c55e" if is_active else "#64748b", bg=card_bg)

        nicknames = self.config_data.get("profile_nicknames", {})
        display_name = nicknames.get(key) or prof.get("display", key.upper())
        cmd_name = get_profile_cli_command(key)
        view["name_lbl"].config(text=f"{display_name} ({cmd_name})", fg=th["accent"] if is_active else th["text"], bg=card_bg, font=self.get_font(9, "bold"))

        raw_email = info.get("email", "Desconhecido")
        email_str = mask_email(raw_email) if self.config_data.get("privacy_mode", False) else raw_email
        view["email_lbl"].config(text=email_str, bg=card_bg, font=self.get_font(8))

        status_text = "✓ Conectado" if info.get("has_oauth") else "⚠️ Reautenticar"
        status_col = "#22c55e" if info.get("has_oauth") else "#eab308"
        view["status_lbl"].config(text=status_text, fg=status_col, bg=card_bg, font=self.get_font(8, "bold"))

        # Update Detail Button state
        is_expanded = self.expanded_cards.get(key, self.all_expanded)
        view["btn_detail"].config(text="▲ Resumo" if is_expanded else "▼ Detalhes", bg=card_bg, font=self.get_font(7, "bold"))

        # Update Badges (Pro / Standard)
        for w in view["badges_box"].winfo_children():
            w.destroy()

        is_pro = info.get("is_pro", False)
        if is_pro:
            pill = tk.Label(view["badges_box"], text="✦ PRO / ARGON", font=self.get_font(7, "bold"),
                            fg="#e9d5ff", bg="#581c87", bd=1, relief="solid", highlightbackground="#9333ea", highlightthickness=1,
                            padx=4, pady=1)
            pill.pack(side="left", padx=(0, 2))
        else:
            pill = tk.Label(view["badges_box"], text="PADRÃO", font=self.get_font(7, "bold"),
                            fg="#94a3b8", bg="#1e293b", padx=4, pady=1)
            pill.pack(side="left", padx=(0, 2))

        # Helper to format in-bar text
        def format_bar_texts(label, used_val, rst_val, icon):
            rem_val = max(100.0 - used_val, 0.0)
            rst_str = pm.format_countdown(rst_val) if isinstance(rst_val, (int, float)) else str(rst_val)
            left_t = f"{icon}{label}  {used_val:4.1f}%"
            if self.config_data.get("show_free_pct", True):
                right_t = f"{rem_val:4.1f}% livre"
                if self.config_data.get("show_countdown", True) and rst_str not in ("pronto", "0m", "0s"):
                    right_t += f" • {rst_str}"
            else:
                right_t = f"reset {rst_str}" if (self.config_data.get("show_countdown", True) and rst_str not in ("pronto", "0m", "0s")) else ""
            return left_t, right_t

        # 1. Update Gemini 5h In-Bar
        l_5h, r_5h = format_bar_texts("Gemini (5h)", used_5h, g5.get("reset_in_seconds", 0), "★ ")
        self.update_compact_bargraph(view["gem5_bar"], used_5h, l_5h, r_5h, theme_color="#38bdf8", track_color="#082f49")

        # 2. Update Gemini 7d Semanal In-Bar
        l_w, r_w = format_bar_texts("Gemini (7d)", used_w, gw.get("reset_in_seconds", 0), "📅 ")
        self.update_compact_bargraph(view["gemw_bar"], used_w, l_w, r_w, theme_color="#0284c7", track_color="#0c4a6e")

        # 3. Update Outros (GPT/Claude) In-Bar
        l_ot, r_ot = format_bar_texts("GPT / Claude", used_ot, ot.get("reset_in_seconds", 0), "⚡ ")
        self.update_compact_bargraph(view["outros_bar"], used_ot, l_ot, r_ot, theme_color="#10b981", track_color="#064e3b")

        # Update dynamic tooltips with exact models and current quota percentages
        tts = getattr(self, "bar_tooltips", {}).get(key, {})
        if "gem5" in tts:
            rst5 = pm.format_countdown(g5.get("reset_in_seconds", 0))
            tts["gem5"].text_func = (
                f"★ COTA GEMINI — Janela 5h ({100.0 - used_5h:.1f}% livre • reset: {rst5})\n"
                "Modelos exatos incluídos:\n"
                "• Gemini 3.8 Flash (Low)\n"
                "• Gemini 3.8 Flash (Medium)\n"
                "• Gemini 3.8 Flash (High)"
            )
        if "gemw" in tts:
            rstw = pm.format_countdown(gw.get("reset_in_seconds", 0))
            tts["gemw"].text_func = (
                f"📅 COTA GEMINI — Semanal 7d ({100.0 - used_w:.1f}% livre • reset: {rstw})\n"
                "Limite semanal global compartilhado:\n"
                "• Gemini 3.8 Flash (Low / Medium / High)"
            )
        if "outros" in tts:
            rsto = pm.format_countdown(ot.get("reset_in_seconds", 0))
            tts["outros"].text_func = (
                f"⚡ COTA GPT / CLAUDE (3P) ({100.0 - used_ot:.1f}% livre • reset: {rsto})\n"
                "Modelos exatos incluídos:\n"
                "• Claude Sonnet 4.6 (Thinking)\n"
                "• Claude Opus 4.6 (Thinking)\n"
                "• GPT-OSS 120B (Medium)"
            )

        # 4. Update Argon In-Bar (Exibe no Pro, esconde completamente nos planos sem Argon)
        if is_pro:
            if not view["argon_row"].winfo_ismapped():
                view["argon_row"].pack(fill="x", pady=1)
            l_ar, r_ar = format_bar_texts("Argon (Pro)", used_ar, ar.get("reset_in_seconds", 0), "✦ ")
            self.update_compact_bargraph(view["argon_bar"], used_ar, l_ar, r_ar, theme_color="#c084fc", track_color="#3b0764")
            if not view["f_arg_det"].winfo_ismapped():
                view["f_arg_det"].pack(fill="x", padx=6, pady=2)
            view["lbl_arg_title"].config(text="✦ Argon (Pro):", fg="#c084fc")
            view["lbl_arg_models"].config(text="Gemini 4 Argon (Low • Medium • High)", fg="#cbd5e1", font=self.get_font(7))
            rsta = pm.format_countdown(ar.get("reset_in_seconds", 0))
            if hasattr(self, "argon_tooltips") and key in self.argon_tooltips:
                self.argon_tooltips[key].text_func = (
                    f"✦ COTA ARGON — Plano Pro Pago ({100.0 - used_ar:.1f}% livre • reset: {rsta})\n"
                    "Modelos exatos incluídos:\n"
                    "• Gemini 4 Argon (Low)\n"
                    "• Gemini 4 Argon (Medium)\n"
                    "• Gemini 4 Argon (High)"
                )
        else:
            # Esconde completamente a barra do Argon e os detalhes nos planos padrão sem Argon!
            if view["argon_row"].winfo_ismapped():
                view["argon_row"].pack_forget()
            if view["f_arg_det"].winfo_ismapped():
                view["f_arg_det"].pack_forget()

        # Update Drawer Visibility
        if is_expanded:
            if not view["drawer"].winfo_ismapped():
                view["drawer"].pack(fill="x", padx=8, pady=(2, 4))
        else:
            if view["drawer"].winfo_ismapped():
                view["drawer"].pack_forget()

        # Update Active tag & button (Preserva a simetria horizontal exata)
        if is_active:
            view["tag_lbl"].pack(side="left", padx=4)
            view["btn_activate"].config(text="✓ Em Uso", bg="#064e3b", fg="#a7f3d0", state="disabled", cursor="arrow")
        else:
            view["tag_lbl"].pack_forget()
            view["btn_activate"].config(text="Ativar", bg="#2e1065", fg="#a855f7", state="normal", cursor="hand2")

    def get_ordered_enabled_profiles(self):
        profiles = pm.discover_profiles()
        saved_order = self.config_data.get("profile_order", [])
        enabled_dict = self.config_data.get("enabled_profiles", {})

        ordered_keys = [k for k in saved_order if k in profiles]
        for k in profiles:
            if k not in ordered_keys:
                ordered_keys.append(k)

        active_keys = [k for k in ordered_keys if enabled_dict.get(k, True)]
        if not active_keys:
            active_keys = ordered_keys

        return active_keys, profiles

    def refresh_profiles(self, force=False):
        active_keys, profiles = self.get_ordered_enabled_profiles()
        active_prof = pm.get_active_profile()

        profile_models = self.config_data.get("profile_models", {})
        models_sig = json.dumps(profile_models, sort_keys=True)
        signature = f"{','.join(active_keys)}|cols={self.cols}|th={self.config_data.get('theme')}|m={models_sig}"

        if force or signature != self.known_profiles_signature:
            self.known_profiles_signature = signature
            for child in self.grid_container.winfo_children():
                child.destroy()
            self.card_views.clear()

            # Configura uniformidade estrita de colunas e linhas para tamanho idêntico
            for c in range(self.cols):
                self.grid_container.grid_columnconfigure(c, weight=1, uniform="profile_cols")
            total_rows = (len(active_keys) + self.cols - 1) // self.cols
            for r in range(max(total_rows, 1)):
                self.grid_container.grid_rowconfigure(r, weight=1, uniform="profile_rows")

            positions = self.config_data.get("profile_positions", {})
            for idx, key in enumerate(active_keys):
                prof = profiles[key]
                if key in positions:
                    r = positions[key].get("row", idx // self.cols)
                    c = positions[key].get("col", idx % self.cols)
                else:
                    r = idx // self.cols
                    c = idx % self.cols
                self.build_profile_card(self.grid_container, key, prof, row=r, col=c)

        best_key = None
        best_rem = -1.0
        connected_count = 0
        pro_count = 0
        nicknames = self.config_data.get("profile_nicknames", {})

        for key in active_keys:
            prof = profiles[key]
            info = pm.get_profile_info(prof)
            is_active = (key == active_prof)
            self.update_card_in_place(key, prof, info, is_active)

            if info.get("has_oauth"):
                connected_count += 1
            if info.get("is_pro"):
                pro_count += 1
            g5 = info.get("gemini_5h") or {}
            rem_5h = max(100.0 - float(g5.get("used_pct", 0.0)), 0.0)
            score = rem_5h + (0.1 if info.get("is_pro") else 0.0)
            if score > best_rem:
                best_rem = score
                best_key = key

        # Update Executive Summary KPI Strip
        if hasattr(self, "kpi_active_lbl"):
            act_disp = nicknames.get(active_prof) or profiles.get(active_prof, {}).get("display", active_prof.upper())
            act_cmd = get_profile_cli_command(active_prof)
            self.kpi_active_lbl.config(text=f"🟢 Ativo: {act_disp} ({act_cmd})")

            if best_key and best_key in profiles:
                self.best_free_profile_key = best_key
                b_disp = nicknames.get(best_key) or profiles[best_key].get("display", best_key.upper())
                b_g5 = pm.get_profile_info(profiles[best_key]).get("gemini_5h") or {}
                b_rem = max(100.0 - float(b_g5.get("used_pct", 0.0)), 0.0)
                self.kpi_best_lbl.config(text=f"💡 Melhor Livre: {b_disp} ({b_rem:.0f}% 5h)")
            else:
                self.best_free_profile_key = None
                self.kpi_best_lbl.config(text="💡 Melhor Livre: --")

            self.kpi_stats_lbl.config(text=f"Conectadas: {connected_count}/{len(active_keys)} • Pro: {pro_count}")

        self.time_lbl.config(text=f"Atualizado: {time.strftime('%H:%M:%S')}")

    def switch_profile_and_refresh(self, profile_key):
        pm.cmd_switch(profile_key)
        self.refresh_profiles()
        if self.tray:
            self.tray.update_tray_menu()

    def prompt_new_profile(self):
        win = tk.Toplevel(self)
        win.title("Novo Perfil Antigravity")
        win.geometry("380x280")
        win.configure(bg="#0f172a")
        win.attributes("-topmost", True)

        tk.Label(win, text="Criar Novo Perfil", font=("Segoe UI", 11, "bold"), fg="#f8fafc", bg="#0f172a").pack(pady=(12, 6))

        f_inputs = tk.Frame(win, bg="#0f172a")
        f_inputs.pack(padx=20, fill="x")

        tk.Label(f_inputs, text="Nome do Perfil (ex: perfil5):", font=("Segoe UI", 8), fg="#94a3b8", bg="#0f172a").pack(anchor="w")
        ent_nome = tk.Entry(f_inputs, font=("Segoe UI", 9), bg="#1e293b", fg="#f8fafc", insertbackground="#f8fafc")
        ent_nome.pack(fill="x", pady=(2, 6))

        tk.Label(f_inputs, text="Email Google (opcional):", font=("Segoe UI", 8), fg="#94a3b8", bg="#0f172a").pack(anchor="w")
        ent_email = tk.Entry(f_inputs, font=("Segoe UI", 9), bg="#1e293b", fg="#f8fafc", insertbackground="#f8fafc")
        ent_email.pack(fill="x", pady=(2, 6))

        def on_create():
            nome = ent_nome.get().strip()
            email = ent_email.get().strip()
            if nome:
                pm.cmd_create(nome, email if email else None)
                win.destroy()
                self.refresh_profiles(force=True)
                if self.tray:
                    self.tray.update_tray_menu()

        tk.Button(win, text="Criar Perfil", font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#0284c7",
                  activebackground="#0369a1", bd=0, padx=14, pady=6, cursor="hand2", command=on_create).pack(pady=14)

    def schedule_next_refresh(self):
        sec = self.config_data.get("refresh_seconds", 15)
        self.after(max(sec, 5) * 1000, self.on_timer_refresh)

    def on_timer_refresh(self):
        try:
            self.refresh_profiles(force=False)
        except Exception:
            pass
        self.schedule_next_refresh()

class TrayApp:
    def __init__(self):
        self.widget = None
        self.icon = None

    def build_tray_menu(self):
        active = pm.get_active_profile()
        profiles = pm.discover_profiles()

        menu_items = [
            item("⚡ Antigravity Monitor", lambda icon, item: self.toggle_widget(), default=True),
            item("⚙️ Configurações Avançadas", lambda icon, item: self.open_settings()),
            Menu.SEPARATOR
        ]

        def make_cmd_action(k):
            return lambda icon, item: open_cmd_for_profile(k)

        def make_desktop_action(k):
            return lambda icon, item: pm.cmd_desktop(k)

        def make_switch_action(k):
            return lambda icon, item: self.switch_and_refresh(k)

        for key, prof in profiles.items():
            is_active = (key == active)
            mark = "● " if is_active else "  "
            cmd_name = get_profile_cli_command(key)
            info = pm.get_profile_info(prof)
            label = f"{mark}{prof['display']} ({cmd_name}) - {info['email']}"

            sub_items = [
                item(f"⚡ Abrir CMD ({cmd_name})", make_cmd_action(key)),
                item("🖥️ Abrir Desktop", make_desktop_action(key)),
                item("🔄 Definir como Ativo", make_switch_action(key))
            ]
            menu_items.append(item(label, Menu(*sub_items)))

        menu_items.extend([
            Menu.SEPARATOR,
            item("➕ Criar Novo Perfil", lambda icon, item: self.open_new_profile_dialog()),
            item("🔄 Atualizar Cotas", lambda icon, item: self.refresh_all()),
            Menu.SEPARATOR,
            item("❌ Sair", lambda icon, item: self.quit_app())
        ])

        return Menu(*menu_items)

    def toggle_widget(self):
        if self.widget:
            self.widget.after(0, self.widget.toggle_visibility)

    def open_settings(self):
        if self.widget:
            self.widget.after(0, self.widget.open_settings)

    def switch_and_refresh(self, profile_key):
        pm.cmd_switch(profile_key)
        if self.widget:
            self.widget.after(0, self.widget.refresh_profiles)
        self.update_tray_menu()

    def refresh_all(self):
        if self.widget:
            self.widget.after(0, lambda: self.widget.refresh_profiles(force=True))
        self.update_tray_menu()

    def open_new_profile_dialog(self):
        if self.widget:
            self.widget.after(0, self.widget.prompt_new_profile)

    def update_tray_menu(self):
        if self.icon:
            self.icon.menu = self.build_tray_menu()

    def quit_app(self):
        if self.icon:
            self.icon.stop()
        if self.widget:
            self.widget.after(0, self.widget.destroy)

    def run(self, server_sock=None):
        self.widget = DesktopWidget(self)

        # Start IPC socket listener to wake up widget when desktop shortcut is clicked!
        if server_sock:
            def ipc_listener_thread():
                while True:
                    try:
                        conn, _ = server_sock.accept()
                        data = conn.recv(1024).decode('utf-8', errors='ignore').strip()
                        if "SHOW" in data:
                            self.widget.after(0, self.widget.bring_to_front)
                        conn.sendall(b"OK\n")
                        conn.close()
                    except Exception:
                        break
            t = threading.Thread(target=ipc_listener_thread, daemon=True)
            t.start()

        tray_img = create_tray_image()
        self.icon = pystray.Icon("agy_toolbar", tray_img, "Antigravity Quota Monitor", menu=self.build_tray_menu())

        tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        tray_thread.start()

        self.widget.mainloop()

def enforce_single_instance_or_wake():
    """
    Enforces that only one instance of the tray app runs using a Win32 Named Mutex
    combined with an IPC TCP socket on localhost:49285.
    If an instance is already running, wakes it up and exits immediately.
    """
    mutex = None
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        mutex = kernel32.CreateMutexW(None, False, SINGLE_INSTANCE_MUTEX)
        last_err = kernel32.GetLastError()
        if last_err == 183:  # ERROR_ALREADY_EXISTS: Check if existing instance is actually alive
            contacted = False
            try:
                client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                client.settimeout(1.5)
                client.connect(("127.0.0.1", SINGLE_INSTANCE_PORT))
                client.sendall(b"SHOW\n")
                ack = client.recv(1024)
                if ack:
                    contacted = True
                client.close()
            except Exception:
                contacted = False

            if contacted:
                # Successfully signaled existing instance!
                sys.exit(0)
            # If not contacted, the previous instance died or hung, so take over!
    except Exception:
        pass

    # We are the master instance! Bind server socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_sock.bind(("127.0.0.1", SINGLE_INSTANCE_PORT))
        server_sock.listen(5)
    except Exception:
        try:
            time.sleep(0.5)
            server_sock.bind(("127.0.0.1", SINGLE_INSTANCE_PORT))
            server_sock.listen(5)
        except Exception:
            server_sock = None

    return mutex, server_sock

if __name__ == "__main__":
    try:
        mutex, server_sock = enforce_single_instance_or_wake()
        app = TrayApp()
        app.run(server_sock)
    except Exception as e:
        import traceback
        log_file = os.path.join(CUSTOM_DIR, "tray.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERRO FATAL:\n")
            f.write(traceback.format_exc())
            f.write("\n")

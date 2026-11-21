import os
import sys
import json
import time
import threading
import subprocess
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageDraw

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CUSTOM_DIR = os.path.join(os.path.expanduser("~"), ".antigravity-custom")
for d in [SCRIPT_DIR, CUSTOM_DIR]:
    if d not in sys.path:
        sys.path.insert(0, d)

try:
    import profile_manager as pm
except ImportError:
    import profile_manager as pm

import pystray
from pystray import MenuItem as item, Menu

CONFIG_FILE = os.path.join(CUSTOM_DIR, "widget_config.json")

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

DEFAULT_WIDGET_CONFIG = {
    "x": 80,
    "y": 80,
    "width": 720,
    "height": 470,
    "always_on_top": True,
    "visible": True,
    "locked": False,
    "grid_preset": "2x2",
    "columns": 2,
    "refresh_seconds": 12,
    "opacity": 0.97,
    "enabled_profiles": {},
    "profile_order": [],
    "profile_positions": {}
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

def get_profile_cli_command(profile_key):
    if profile_key == "perfil1":
        return "agy"
    if profile_key.startswith("perfil") and profile_key[6:].isdigit():
        return f"agy{profile_key[6:]}"
    if profile_key.isdigit():
        return f"agy{profile_key}" if profile_key != "1" else "agy"
    return f"agy-{profile_key}"

def open_cmd_for_profile(profile_key):
    cmd_name = get_profile_cli_command(profile_key)
    profiles = pm.discover_profiles()
    prof = profiles.get(profile_key, {})
    disp = prof.get("display", profile_key.upper())

    startup_line = f'title Antigravity CLI [{disp}] && echo ======================================================== && echo   ANTIGRAVITY CLI - {disp} && echo   Comando: {cmd_name} && echo ======================================================== && echo. && {cmd_name}'
    subprocess.Popen(f'start cmd.exe /k "{startup_line}"', shell=True)

def create_tray_image(color=(56, 189, 248)):
    img = Image.new("RGBA", (64, 64), color=(0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle([4, 4, 60, 60], radius=14, fill=(15, 23, 42, 240), outline=color, width=3)
    d.ellipse([20, 20, 44, 44], fill=color)
    d.ellipse([26, 26, 38, 38], fill=(15, 23, 42))
    d.ellipse([29, 29, 35, 35], fill=color)
    return img

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
        self.title("Ajustes do Widget & Perfis")
        self.geometry("460x520")
        self.configure(bg="#0f172a")
        self.attributes("-topmost", True)
        self.resizable(False, False)

        self.config_copy = parent.config_data.copy()
        self.build_ui()

    def build_ui(self):
        # Header
        h = tk.Frame(self, bg="#1e293b", height=42)
        h.pack(fill="x")
        tk.Label(h, text="⚙️ Configurações do Antigravity Widget", font=("Segoe UI", 11, "bold"), fg="#f8fafc", bg="#1e293b").pack(side="left", padx=14, pady=10)

        main_f = tk.Frame(self, bg="#0f172a")
        main_f.pack(fill="both", expand=True, padx=16, pady=10)

        # 1. Grid Preset Selection
        tk.Label(main_f, text="📐 Layout & Disposição em Grade:", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w", pady=(4, 2))
        f_grid = tk.Frame(main_f, bg="#0f172a")
        f_grid.pack(fill="x", pady=2)

        self.preset_var = tk.StringVar(value=self.config_copy.get("grid_preset", "2x2"))
        presets_list = list(GRID_PRESETS.keys())
        self.cb_preset = ttk.Combobox(f_grid, textvariable=self.preset_var, values=presets_list, state="readonly", width=12, font=("Segoe UI", 9))
        self.cb_preset.pack(side="left")

        tk.Label(f_grid, text=" (ex: 2x2 = 2 em cima, 2 embaixo; 1x4 = coluna única)", font=("Segoe UI", 8), fg="#64748b", bg="#0f172a").pack(side="left", padx=6)

        # 2. Refresh Time Slider
        tk.Label(main_f, text="⏱ Tempo de Atualização (Segundos):", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w", pady=(12, 2))
        f_ref = tk.Frame(main_f, bg="#0f172a")
        f_ref.pack(fill="x")

        self.ref_var = tk.IntVar(value=self.config_copy.get("refresh_seconds", 12))
        self.ref_lbl = tk.Label(f_ref, text=f"{self.ref_var.get()}s", font=("Segoe UI", 9, "bold"), fg="#22c55e", bg="#0f172a", width=5)
        self.ref_lbl.pack(side="right")

        scale_ref = tk.Scale(f_ref, from_=5, to=60, orient="horizontal", variable=self.ref_var, bg="#1e293b", fg="#f8fafc",
                             highlightthickness=0, bd=0, activebackground="#38bdf8", command=lambda v: self.ref_lbl.config(text=f"{v}s"))
        scale_ref.pack(fill="x", side="left", expand=True)

        # 3. Window Opacity Slider
        tk.Label(main_f, text="✨ Opacidade da Janela:", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w", pady=(12, 2))
        f_op = tk.Frame(main_f, bg="#0f172a")
        f_op.pack(fill="x")

        cur_op = int(self.config_copy.get("opacity", 0.97) * 100)
        self.op_var = tk.IntVar(value=cur_op)
        self.op_lbl = tk.Label(f_op, text=f"{cur_op}%", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a", width=5)
        self.op_lbl.pack(side="right")

        scale_op = tk.Scale(f_op, from_=70, to=100, orient="horizontal", variable=self.op_var, bg="#1e293b", fg="#f8fafc",
                            highlightthickness=0, bd=0, activebackground="#38bdf8", command=lambda v: self.op_lbl.config(text=f"{v}%"))
        scale_op.pack(fill="x", side="left", expand=True)

        # 4. Profile Management (Toggle & Reorder)
        tk.Label(main_f, text="👥 Gerenciamento & Ordem dos Perfis:", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#0f172a").pack(anchor="w", pady=(14, 2))
        tk.Label(main_f, text="Marque para ativar/desativar e use as setas para reordenar blocos:", font=("Segoe UI", 8), fg="#64748b", bg="#0f172a").pack(anchor="w")

        f_prof = tk.Frame(main_f, bg="#0f172a")
        f_prof.pack(fill="both", expand=True, pady=4)

        # List of profiles with order
        all_profiles = pm.discover_profiles()
        saved_order = self.config_copy.get("profile_order", [])
        
        # Merge existing with order
        self.ordered_keys = [k for k in saved_order if k in all_profiles]
        for k in all_profiles:
            if k not in self.ordered_keys:
                self.ordered_keys.append(k)

        self.listbox = tk.Listbox(f_prof, font=("Segoe UI", 9), bg="#1e293b", fg="#f8fafc", selectbackground="#0284c7",
                                  bd=1, relief="solid", highlightthickness=0, height=5)
        self.listbox.pack(side="left", fill="both", expand=True)

        enabled_dict = self.config_copy.get("enabled_profiles", {})
        self.refresh_listbox(all_profiles, enabled_dict)

        # Buttons on right of listbox
        f_btns = tk.Frame(f_prof, bg="#0f172a")
        f_btns.pack(side="right", padx=(8, 0))

        tk.Button(f_btns, text="▲ Subir", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg="#334155", bd=0, padx=8, pady=3,
                  cursor="hand2", command=self.move_up).pack(fill="x", pady=2)
        tk.Button(f_btns, text="▼ Descer", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg="#334155", bd=0, padx=8, pady=3,
                  cursor="hand2", command=self.move_down).pack(fill="x", pady=2)
        tk.Button(f_btns, text="👁 Toggle", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg="#0c4a6e", bd=0, padx=8, pady=3,
                  cursor="hand2", command=self.toggle_enable).pack(fill="x", pady=(6, 2))

        # Bottom Action Bar
        f_act = tk.Frame(self, bg="#1e293b", height=44)
        f_act.pack(fill="x", side="bottom")

        tk.Button(f_act, text="Salvar e Aplicar", font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#0284c7",
                  activebackground="#0369a1", activeforeground="#ffffff", bd=0, padx=16, pady=5, cursor="hand2",
                  command=self.save_and_apply).pack(side="right", padx=14, pady=8)

        tk.Button(f_act, text="Cancelar", font=("Segoe UI", 9), fg="#94a3b8", bg="#1e293b",
                  bd=0, padx=12, pady=5, cursor="hand2", command=self.destroy).pack(side="right", padx=6, pady=8)

    def refresh_listbox(self, all_profiles, enabled_dict):
        self.listbox.delete(0, tk.END)
        for k in self.ordered_keys:
            is_en = enabled_dict.get(k, True)
            mark = "☑" if is_en else "☐"
            prof = all_profiles.get(k, {})
            disp = prof.get("display", k)
            self.listbox.insert(tk.END, f" {mark}  {disp} ({k})")

    def move_up(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] == 0:
            return
        idx = sel[0]
        self.ordered_keys[idx], self.ordered_keys[idx - 1] = self.ordered_keys[idx - 1], self.ordered_keys[idx]
        self.refresh_listbox(pm.discover_profiles(), self.config_copy.get("enabled_profiles", {}))
        self.listbox.selection_set(idx - 1)

    def move_down(self):
        sel = self.listbox.curselection()
        if not sel or sel[0] >= len(self.ordered_keys) - 1:
            return
        idx = sel[0]
        self.ordered_keys[idx], self.ordered_keys[idx + 1] = self.ordered_keys[idx + 1], self.ordered_keys[idx]
        self.refresh_listbox(pm.discover_profiles(), self.config_copy.get("enabled_profiles", {}))
        self.listbox.selection_set(idx + 1)

    def toggle_enable(self):
        sel = self.listbox.curselection()
        if not sel:
            return
        k = self.ordered_keys[sel[0]]
        en_dict = self.config_copy.get("enabled_profiles", {})
        cur = en_dict.get(k, True)
        en_dict[k] = not cur
        self.config_copy["enabled_profiles"] = en_dict
        self.refresh_listbox(pm.discover_profiles(), en_dict)
        self.listbox.selection_set(sel[0])

    def save_and_apply(self):
        preset = self.preset_var.get()
        if preset in GRID_PRESETS:
            cols, rows = GRID_PRESETS[preset]
            self.parent.cols = cols
            self.config_copy["grid_preset"] = preset
            self.config_copy["columns"] = cols

            # Calculate optimal window size
            opt_w = min(max(cols * 350 + 20, 360), 1600)
            opt_h = min(max(rows * 190 + 90, 240), 1000)
            self.parent.geometry(f"{opt_w}x{opt_h}")
            self.config_copy["width"] = opt_w
            self.config_copy["height"] = opt_h

        self.config_copy["refresh_seconds"] = self.ref_var.get()
        self.config_copy["opacity"] = self.op_var.get() / 100.0
        self.config_copy["profile_order"] = self.ordered_keys

        self.parent.config_data.update(self.config_copy)
        self.parent.attributes("-alpha", self.config_copy["opacity"])
        save_widget_config(self.parent.config_data)

        self.parent.grid_btn.config(text=f"⊞ {preset}")
        self.parent.refresh_profiles(force=True)
        self.destroy()

class DesktopWidget(tk.Tk):
    def __init__(self, tray_controller):
        super().__init__()
        self.tray = tray_controller
        self.config_data = load_widget_config()

        self.title("Antigravity Quota Monitor")
        self.configure(bg="#0f172a") # Slate 900
        self.overrideredirect(True)   # Borderless sleek frame
        self.attributes("-topmost", self.config_data.get("always_on_top", True))
        self.attributes("-alpha", self.config_data.get("opacity", 0.97))

        self.cols = self.config_data.get("columns", 2)
        cur_w = self.config_data.get("width", 720)
        cur_h = self.config_data.get("height", 470)
        self.geometry(f"{cur_w}x{cur_h}+{self.config_data.get('x', 80)}+{self.config_data.get('y', 80)}")

        self._offset_x = 0
        self._offset_y = 0

        self.card_views = {}
        self.known_profiles_signature = ""

        self.build_ui()
        self.bind_events()
        self.refresh_profiles(force=True)
        self.start_auto_refresh()

    def build_ui(self):
        # Outer border frame
        self.outer_frame = tk.Frame(self, bg="#1e293b", bd=2, relief="solid")
        self.outer_frame.pack(fill="both", expand=True)

        # Header Bar
        self.header = tk.Frame(self.outer_frame, bg="#1e293b", height=42)
        self.header.pack(fill="x", side="top", padx=12, pady=(8, 4))

        title_box = tk.Frame(self.header, bg="#1e293b")
        title_box.pack(side="left")

        tk.Label(title_box, text="✦", font=("Segoe UI", 13, "bold"), fg="#38bdf8", bg="#1e293b").pack(side="left", padx=(0, 5))
        tk.Label(title_box, text="ANTIGRAVITY", font=("Segoe UI", 11, "bold"), fg="#f8fafc", bg="#1e293b").pack(side="left")
        tk.Label(title_box, text="QUOTAS", font=("Segoe UI", 9, "bold"), fg="#38bdf8", bg="#1e293b").pack(side="left", padx=3)

        # Controls on header
        ctrl_box = tk.Frame(self.header, bg="#1e293b")
        ctrl_box.pack(side="right")

        # 1. Settings Button (NEW!)
        self.settings_btn = tk.Label(ctrl_box, text="⚙️ Config", font=("Segoe UI", 8, "bold"), fg="#f8fafc", bg="#0284c7",
                                     padx=7, pady=2, cursor="hand2")
        self.settings_btn.pack(side="left", padx=4)
        self.settings_btn.bind("<Button-1>", lambda e: self.open_settings())

        # 2. Preset Grid Indicator / Quick Switch
        preset_name = self.config_data.get("grid_preset", "2x2")
        self.grid_btn = tk.Label(ctrl_box, text=f"⊞ {preset_name}", font=("Segoe UI", 8, "bold"), fg="#cbd5e1", bg="#334155",
                                 padx=6, pady=2, cursor="hand2")
        self.grid_btn.pack(side="left", padx=4)
        self.grid_btn.bind("<Button-1>", lambda e: self.quick_cycle_grid())

        # 3. Lock / Unlock
        is_locked = self.config_data.get("locked", False)
        lock_txt = "🔒 Fixado" if is_locked else "🔓 Mover"
        lock_fg = "#38bdf8" if is_locked else "#94a3b8"
        self.lock_btn = tk.Label(ctrl_box, text=lock_txt, font=("Segoe UI", 8, "bold"), fg=lock_fg, bg="#334155", padx=6, pady=2, cursor="hand2")
        self.lock_btn.pack(side="left", padx=4)
        self.lock_btn.bind("<Button-1>", lambda e: self.toggle_lock())

        # 4. Pin (Always on top)
        is_pin = self.config_data.get("always_on_top", True)
        self.pin_btn = tk.Label(ctrl_box, text="📌" if is_pin else "📍", font=("Segoe UI", 10), fg="#94a3b8", bg="#1e293b", cursor="hand2")
        self.pin_btn.pack(side="left", padx=4)
        self.pin_btn.bind("<Button-1>", lambda e: self.toggle_pin())

        # 5. Hide
        close_btn = tk.Label(ctrl_box, text="✕", font=("Segoe UI", 11, "bold"), fg="#94a3b8", bg="#1e293b", cursor="hand2")
        close_btn.pack(side="left", padx=(4, 0))
        close_btn.bind("<Button-1>", lambda e: self.hide_widget())

        # Scrollable Canvas for Profiles Grid (supports resizing!)
        self.canvas = tk.Canvas(self.outer_frame, bg="#0f172a", bd=0, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=8, pady=4)

        self.grid_container = tk.Frame(self.canvas, bg="#0f172a")
        self.canvas_window = self.canvas.create_window((0, 0), window=self.grid_container, anchor="nw")
        
        self.grid_container.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.canvas_window, width=e.width))

        # Footer Bar with Resize Handle
        self.footer = tk.Frame(self.outer_frame, bg="#1e293b", height=34)
        self.footer.pack(fill="x", side="bottom", padx=8, pady=(2, 6))

        self.time_lbl = tk.Label(self.footer, text="Atualizado", font=("Segoe UI", 8), fg="#64748b", bg="#1e293b")
        self.time_lbl.pack(side="left", padx=4)

        # Resize grip in bottom-right corner!
        self.resize_grip = ResizeGrip(self.footer, self)
        self.resize_grip.pack(side="right", padx=(2, 0))

        btn_refresh = tk.Label(self.footer, text="🔄 Atualizar", font=("Segoe UI", 8, "bold"), fg="#38bdf8", bg="#1e293b", cursor="hand2")
        btn_refresh.pack(side="right", padx=6)
        btn_refresh.bind("<Button-1>", lambda e: self.refresh_profiles(force=True))

        btn_new = tk.Label(self.footer, text="➕ Novo Perfil", font=("Segoe UI", 8, "bold"), fg="#a855f7", bg="#1e293b", cursor="hand2")
        btn_new.pack(side="right", padx=6)
        btn_new.bind("<Button-1>", lambda e: self.prompt_new_profile())

    def bind_events(self):
        for widget in [self.header, self.outer_frame]:
            widget.bind("<ButtonPress-1>", self.on_drag_start)
            widget.bind("<B1-Motion>", self.on_drag_motion)
            widget.bind("<ButtonRelease-1>", self.on_drag_end)

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
        self.lock_btn.config(text="🔒 Fixado" if new_val else "🔓 Mover", fg="#38bdf8" if new_val else "#94a3b8")
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
        # Quick cycle through popular presets: 2x2 -> 1x4 -> 4x1 -> 1x2 -> 2x2
        cycle = ["2x2", "1x4", "4x1", "1x2", "2x1", "2x3", "3x2"]
        cur = self.config_data.get("grid_preset", "2x2")
        next_idx = (cycle.index(cur) + 1) % len(cycle) if cur in cycle else 0
        new_preset = cycle[next_idx]

        cols, rows = GRID_PRESETS[new_preset]
        self.cols = cols
        self.config_data["grid_preset"] = new_preset
        self.config_data["columns"] = cols

        opt_w = min(max(cols * 350 + 20, 360), 1600)
        opt_h = min(max(rows * 190 + 90, 240), 1000)
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

    def create_dual_progressbar(self, parent, width=200, height=8):
        cv = tk.Canvas(parent, width=width, height=height, bg="#334155", bd=0, highlightthickness=0)
        fill_id = cv.create_rectangle(0, 0, 0, height, fill="#22c55e", width=0)
        return cv, fill_id

    def update_dual_progressbar(self, cv, fill_id, pct, width=200, height=8):
        pct = min(max(pct, 0.0), 100.0)
        fill_w = int((pct / 100.0) * width)
        col = "#22c55e" if pct < 60 else ("#eab308" if pct < 85 else "#ef4444")
        cv.coords(fill_id, 0, 0, fill_w, height)
        cv.itemconfig(fill_id, fill=col)

    def build_profile_card(self, parent, key, prof, row, col):
        is_active = (key == pm.get_active_profile())
        card_bg = "#172554" if is_active else "#1e293b"
        border_col = "#38bdf8" if is_active else "#334155"

        card = tk.Frame(parent, bg=card_bg, bd=1, relief="solid", highlightbackground=border_col, highlightthickness=1)
        card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
        parent.grid_columnconfigure(col, weight=1)

        # Header Row
        row_top = tk.Frame(card, bg=card_bg)
        row_top.pack(fill="x", padx=8, pady=(6, 2))

        dot_lbl = tk.Label(row_top, text="●", font=("Segoe UI", 9), fg="#22c55e" if is_active else "#64748b", bg=card_bg)
        dot_lbl.pack(side="left", padx=(0, 4))

        cmd_name = get_profile_cli_command(key)
        name_lbl = tk.Label(row_top, text=f"{prof['display']}", font=("Segoe UI", 9, "bold"), fg="#f8fafc", bg=card_bg)
        name_lbl.pack(side="left")

        tag_lbl = tk.Label(row_top, text="ATIVO", font=("Segoe UI", 7, "bold"), fg="#38bdf8", bg="#0c4a6e", padx=3, pady=0)
        if is_active:
            tag_lbl.pack(side="left", padx=5)

        # Quick Reorder Arrows on Top-Right of Card! (◀ / ▶)
        reorder_box = tk.Frame(row_top, bg=card_bg)
        reorder_box.pack(side="right")

        btn_left = tk.Label(reorder_box, text="◀", font=("Segoe UI", 8), fg="#64748b", bg=card_bg, cursor="hand2")
        btn_left.pack(side="left", padx=1)
        btn_left.bind("<Button-1>", lambda e, p=key: self.shift_profile_order(p, -1))

        btn_right = tk.Label(reorder_box, text="▶", font=("Segoe UI", 8), fg="#64748b", bg=card_bg, cursor="hand2")
        btn_right.pack(side="left", padx=1)
        btn_right.bind("<Button-1>", lambda e, p=key: self.shift_profile_order(p, 1))

        # Email & Status Row
        row_email = tk.Frame(card, bg=card_bg)
        row_email.pack(fill="x", padx=8, pady=(0, 4))

        email_lbl = tk.Label(row_email, text="Carregando...", font=("Segoe UI", 8), fg="#94a3b8", bg=card_bg)
        email_lbl.pack(side="left")

        status_lbl = tk.Label(row_email, text="", font=("Segoe UI", 7, "bold"), fg="#22c55e", bg=card_bg)
        status_lbl.pack(side="right")

        # Quota 5h Container (Shows % usada AND % livre!)
        q5_box = tk.Frame(card, bg=card_bg)
        q5_box.pack(fill="x", padx=8, pady=(2, 1))

        q5_lbl = tk.Label(q5_box, text="5h: 0.0% usada │ 100.0% livre", font=("Segoe UI", 8), fg="#cbd5e1", bg=card_bg, anchor="w")
        q5_lbl.pack(fill="x")

        q5_bar_row = tk.Frame(card, bg=card_bg)
        q5_bar_row.pack(fill="x", padx=8, pady=(1, 2))
        q5_cv, q5_fill_id = self.create_dual_progressbar(q5_bar_row, width=200, height=8)
        q5_cv.pack(side="left", fill="x", expand=True)
        q5_rst_lbl = tk.Label(q5_bar_row, text="reset: --", font=("Segoe UI", 7), fg="#64748b", bg=card_bg)
        q5_rst_lbl.pack(side="right", padx=(4, 0))

        # Quota 7d Container (Shows % usada AND % livre!)
        qw_box = tk.Frame(card, bg=card_bg)
        qw_box.pack(fill="x", padx=8, pady=(2, 1))

        qw_lbl = tk.Label(qw_box, text="7d: 0.0% usada │ 100.0% livre", font=("Segoe UI", 8), fg="#cbd5e1", bg=card_bg, anchor="w")
        qw_lbl.pack(fill="x")

        qw_bar_row = tk.Frame(card, bg=card_bg)
        qw_bar_row.pack(fill="x", padx=8, pady=(1, 4))
        qw_cv, qw_fill_id = self.create_dual_progressbar(qw_bar_row, width=200, height=8)
        qw_cv.pack(side="left", fill="x", expand=True)
        qw_rst_lbl = tk.Label(qw_bar_row, text="reset: --", font=("Segoe UI", 7), fg="#64748b", bg=card_bg)
        qw_rst_lbl.pack(side="right", padx=(4, 0))

        # Action Buttons Row
        btn_box = tk.Frame(card, bg=card_bg)
        btn_box.pack(fill="x", padx=8, pady=(4, 6))

        btn_cmd = tk.Button(btn_box, text=f"⚡ Abrir CMD ({cmd_name})", font=("Segoe UI", 8, "bold"), fg="#ffffff", bg="#0284c7",
                            activebackground="#0369a1", activeforeground="#ffffff", bd=0, padx=8, pady=3, cursor="hand2",
                            command=lambda p=key: open_cmd_for_profile(p))
        btn_cmd.pack(side="left")

        btn_desktop = tk.Button(btn_box, text="🖥️ Desktop", font=("Segoe UI", 8), fg="#cbd5e1", bg="#334155",
                                activebackground="#475569", activeforeground="#ffffff", bd=0, padx=6, pady=3, cursor="hand2",
                                command=lambda p=key: pm.cmd_desktop(p))
        btn_desktop.pack(side="left", padx=4)

        btn_activate = tk.Button(btn_box, text="Ativar", font=("Segoe UI", 8), fg="#a855f7", bg="#2e1065",
                                 activebackground="#3b0764", activeforeground="#ffffff", bd=0, padx=6, pady=3, cursor="hand2",
                                 command=lambda p=key: self.switch_profile_and_refresh(p))
        if not is_active:
            btn_activate.pack(side="right")

        card.bind("<Double-Button-1>", lambda e, p=key: open_cmd_for_profile(p))

        self.card_views[key] = {
            "card": card,
            "dot_lbl": dot_lbl,
            "name_lbl": name_lbl,
            "tag_lbl": tag_lbl,
            "email_lbl": email_lbl,
            "status_lbl": status_lbl,
            "q5_lbl": q5_lbl,
            "q5_cv": q5_cv,
            "q5_fill_id": q5_fill_id,
            "q5_rst_lbl": q5_rst_lbl,
            "qw_lbl": qw_lbl,
            "qw_cv": qw_cv,
            "qw_fill_id": qw_fill_id,
            "qw_rst_lbl": qw_rst_lbl,
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
        view = self.card_views.get(key)
        if not view:
            return

        card_bg = "#172554" if is_active else "#1e293b"
        border_col = "#38bdf8" if is_active else "#334155"

        view["card"].config(bg=card_bg, highlightbackground=border_col)
        view["dot_lbl"].config(fg="#22c55e" if is_active else "#64748b", bg=card_bg)
        view["email_lbl"].config(text=f"👤 {info['email']}", bg=card_bg)

        status_txt = "✓ Conectado" if info["has_oauth"] else "! Requer Auth"
        status_col = "#22c55e" if info["has_oauth"] else "#f59e0b"
        view["status_lbl"].config(text=status_txt, fg=status_col, bg=card_bg)

        # Quota 5h
        q5h = info["quota_5h"] or {}
        used_5h = float(q5h.get("used_pct", 0.0))
        rem_5h = max(100.0 - used_5h, 0.0)
        rst_5h = pm.format_countdown(q5h.get("reset_in_seconds", 0))

        view["q5_lbl"].config(text=f"⏳ 5h: {used_5h:4.1f}% usada │ {rem_5h:4.1f}% livre", bg=card_bg)
        self.update_dual_progressbar(view["q5_cv"], view["q5_fill_id"], used_5h, width=200, height=8)
        view["q5_rst_lbl"].config(text=f"reset: {rst_5h}", bg=card_bg)

        # Quota 7d
        qw = info["quota_weekly"] or {}
        used_w = float(qw.get("used_pct", 0.0))
        rem_w = max(100.0 - used_w, 0.0)
        rst_w = pm.format_countdown(qw.get("reset_in_seconds", 0))

        view["qw_lbl"].config(text=f"📅 7d: {used_w:4.1f}% usada │ {rem_w:4.1f}% livre", bg=card_bg)
        self.update_dual_progressbar(view["qw_cv"], view["qw_fill_id"], used_w, width=200, height=8)
        view["qw_rst_lbl"].config(text=f"reset: {rst_w}", bg=card_bg)

        if is_active:
            view["tag_lbl"].pack(side="left", padx=5)
            view["btn_activate"].pack_forget()
        else:
            view["tag_lbl"].pack_forget()
            view["btn_activate"].pack(side="right")

    def get_ordered_enabled_profiles(self):
        profiles = pm.discover_profiles()
        saved_order = self.config_data.get("profile_order", [])
        enabled_dict = self.config_data.get("enabled_profiles", {})

        ordered_keys = [k for k in saved_order if k in profiles]
        for k in profiles:
            if k not in ordered_keys:
                ordered_keys.append(k)

        # Filter only enabled
        active_keys = [k for k in ordered_keys if enabled_dict.get(k, True)]
        # Ensure at least 1 profile is shown
        if not active_keys:
            active_keys = ordered_keys

        return active_keys, profiles

    def refresh_profiles(self, force=False):
        active_keys, profiles = self.get_ordered_enabled_profiles()
        active_prof = pm.get_active_profile()

        signature = f"{','.join(active_keys)}|cols={self.cols}"

        if force or signature != self.known_profiles_signature:
            self.known_profiles_signature = signature
            for child in self.grid_container.winfo_children():
                child.destroy()
            self.card_views.clear()

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

        for key in active_keys:
            prof = profiles[key]
            info = pm.get_profile_info(prof)
            is_active = (key == active_prof)
            self.update_card_in_place(key, prof, info, is_active)

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

        tk.Label(f_inputs, text="Posicionamento no Widget:", font=("Segoe UI", 8), fg="#94a3b8", bg="#0f172a").pack(anchor="w")
        pos_var = tk.StringVar(value="auto")
        rb1 = tk.Radiobutton(f_inputs, text="Automático (Preencher Grid)", variable=pos_var, value="auto", font=("Segoe UI", 8), fg="#cbd5e1", bg="#0f172a", selectcolor="#1e293b")
        rb1.pack(anchor="w")
        rb2 = tk.Radiobutton(f_inputs, text="Na linha de baixo (Nova linha)", variable=pos_var, value="new_row", font=("Segoe UI", 8), fg="#cbd5e1", bg="#0f172a", selectcolor="#1e293b")
        rb2.pack(anchor="w")

        def on_create():
            nome = ent_nome.get().strip()
            email = ent_email.get().strip()
            if nome:
                pm.cmd_create(nome, email if email else None)
                
                # Add to profile order
                order = self.config_data.get("profile_order", [])
                if nome not in order:
                    order.append(nome)
                    self.config_data["profile_order"] = order

                if pos_var.get() == "new_row":
                    positions = self.config_data.get("profile_positions", {})
                    current_rows = [p.get("row", 0) for p in positions.values()] or [0]
                    positions[nome] = {"row": max(current_rows) + 1, "col": 0}
                    self.config_data["profile_positions"] = positions
                
                save_widget_config(self.config_data)

                win.destroy()
                self.refresh_profiles(force=True)
                if self.tray:
                    self.tray.update_tray_menu()

        tk.Button(win, text="Criar Perfil", font=("Segoe UI", 9, "bold"), fg="#ffffff", bg="#0284c7", bd=0, padx=12, pady=4, cursor="hand2", command=on_create).pack(pady=10)

    def start_auto_refresh(self):
        self.refresh_profiles()
        sec = self.config_data.get("refresh_seconds", 12) * 1000
        self.after(sec, self.start_auto_refresh)

class TrayApp:
    def __init__(self):
        self.widget = None
        self.icon = None

    def build_tray_menu(self):
        profiles = pm.discover_profiles()
        active = pm.get_active_profile()

        menu_items = [
            item("📊 Mostrar / Ocultar Widget", lambda icon, item: self.toggle_widget(), default=True),
            item("⚙️ Configurações do Widget", lambda icon, item: self.open_settings()),
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

    def run(self):
        self.widget = DesktopWidget(self)

        tray_img = create_tray_image()
        self.icon = pystray.Icon("agy_toolbar", tray_img, "Antigravity Quota Monitor", menu=self.build_tray_menu())

        tray_thread = threading.Thread(target=self.icon.run, daemon=True)
        tray_thread.start()

        self.widget.mainloop()

if __name__ == "__main__":
    try:
        app = TrayApp()
        app.run()
    except Exception as e:
        import traceback
        log_file = os.path.join(CUSTOM_DIR, "tray.log")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] ERRO FATAL:\n")
            f.write(traceback.format_exc())
            f.write("\n")

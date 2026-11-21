import os
import sys
from PIL import Image, ImageDraw

custom_dir = os.path.join(os.path.expanduser("~"), ".antigravity-custom")
os.makedirs(custom_dir, exist_ok=True)
ico_path = os.path.join(custom_dir, "tray.ico")

# 1. Create high-resolution .ico icon
img = Image.new("RGBA", (256, 256), color=(0, 0, 0, 0))
d = ImageDraw.Draw(img)
d.rounded_rectangle([16, 16, 240, 240], radius=50, fill=(15, 23, 42, 255), outline=(56, 189, 248), width=12)
d.ellipse([70, 70, 186, 186], fill=(56, 189, 248))
d.ellipse([95, 95, 161, 161], fill=(15, 23, 42))
d.ellipse([110, 110, 146, 146], fill=(56, 189, 248))
img.save(ico_path, format="ICO", sizes=[(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)])
print("[✓] Created icon:", ico_path)

# 2. Find Desktop directory
desktop_dir = os.path.join(os.path.expanduser("~"), "OneDrive", "Desktop")
if not os.path.exists(desktop_dir):
    desktop_dir = os.path.join(os.path.expanduser("~"), "Desktop")

shortcut_path = os.path.join(desktop_dir, "Antigravity Quotas.lnk")

# 3. Create shortcut using WScript.Shell via COM or VBScript
pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
if not os.path.exists(pythonw_path):
    pythonw_path = "pythonw.exe"

target_script = os.path.join(custom_dir, "tray_app.pyw")

try:
    import win32com.client
    shell = win32com.client.Dispatch("WScript.Shell")
    shortcut = shell.CreateShortcut(shortcut_path)
    shortcut.TargetPath = pythonw_path
    shortcut.Arguments = f'"{target_script}"'
    shortcut.WorkingDirectory = custom_dir
    shortcut.IconLocation = f"{ico_path},0"
    shortcut.Description = "Antigravity Quota Monitor & Profile Manager"
    shortcut.Save()
    print("[✓] Shortcut created successfully at:", shortcut_path)
except Exception as e:
    print("[!] Fallback to PowerShell shortcut creation:", e)
    ps_cmd = f"""
    $WshShell = New-Object -ComObject WScript.Shell
    $Shortcut = $WshShell.CreateShortcut("{shortcut_path}")
    $Shortcut.TargetPath = "{pythonw_path}"
    $Shortcut.Arguments = '"{target_script}"'
    $Shortcut.WorkingDirectory = "{custom_dir}"
    $Shortcut.IconLocation = "{ico_path},0"
    $Shortcut.Description = "Antigravity Quota Monitor & Profile Manager"
    $Shortcut.Save()
    """
    import subprocess
    subprocess.run(["powershell", "-Command", ps_cmd])
    print("[✓] Shortcut created via PowerShell at:", shortcut_path)

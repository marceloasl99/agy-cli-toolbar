"""Update widget_config to properly enable all 6 profiles including agy5 and agy6."""
import json

cfg_path = r"C:\Users\ma038\.antigravity-custom\widget_config.json"
with open(cfg_path, "r", encoding="utf-8") as f:
    cfg = json.load(f)

# Ensure all 6 real profiles are enabled, remove stale "AstroML" entry
cfg["enabled_profiles"] = {
    "perfil1": True,
    "perfil2": True,
    "perfil3": True,
    "perfil4": True,
    "agy5": True,
    "agy6": True,
}
cfg["profile_order"] = ["perfil1", "perfil2", "perfil3", "perfil4", "agy5", "agy6"]
# Keep in 2x2 by default; user can toggle to 3x2 via button
cfg["grid_preset"] = "2x2"
cfg["columns"] = 2

with open(cfg_path, "w", encoding="utf-8") as f:
    json.dump(cfg, f, indent=2, ensure_ascii=False)
print("[OK] widget_config.json updated — 6 profiles enabled")
print("enabled_profiles:", cfg["enabled_profiles"])
print("profile_order:", cfg["profile_order"])

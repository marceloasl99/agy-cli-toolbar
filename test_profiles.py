import os, sys
sys.path.insert(0, r'C:\Users\ma038\.antigravity-custom')
import profile_manager as pm
profiles = pm.discover_profiles()
for k, v in profiles.items():
    info = pm.get_profile_info(v)
    print(k, "email:", info["email"], "has_oauth:", info["has_oauth"], "is_pro:", info["is_pro"])

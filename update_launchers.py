import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import profile_manager as pm

if __name__ == "__main__":
    pm.write_all_launchers()

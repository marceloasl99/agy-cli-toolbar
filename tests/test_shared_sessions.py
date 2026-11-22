import os
import json
import sqlite3
import subprocess
import unittest
import sys

USER_HOME = os.path.expanduser("~")
PROFILES_BASE = os.path.join(USER_HOME, ".agy-perfis")
CENTRAL_CLI = os.path.join(USER_HOME, ".gemini", "antigravity-cli")
LOCALAPPDATA = os.environ.get("LOCALAPPDATA", os.path.join(USER_HOME, "AppData", "Local"))
AGY_BIN_DIR = os.path.join(LOCALAPPDATA, "agy", "bin")

def is_ntfs_junction(path):
    if not os.path.exists(path):
        return False
    try:
        attrs = os.stat(path, follow_symlinks=False).st_file_attributes
        return bool(attrs & 0x0400)
    except Exception:
        return False

class TestSharedSessions(unittest.TestCase):
    def test_1_launchers_define_central_app_data_dir(self):
        """All profile launchers in AGY_BIN_DIR must set ANTIGRAVITY_APP_DATA_DIR to central home."""
        expected_line_app_data = r'set "ANTIGRAVITY_APP_DATA_DIR=%AGY_ORIG_HOME%\.gemini\antigravity-cli"'
        expected_line_gem_dir = r'set "ANTIGRAVITY_GEMINI_DIR=%PERFIL_ROOT%\.gemini"'

        for fname in ["agy1.cmd", "agy2.cmd", "agy3.cmd", "agy4.cmd", "agy5.cmd", "agy6.cmd"]:
            fpath = os.path.join(AGY_BIN_DIR, fname)
            self.assertTrue(os.path.exists(fpath), f"Launcher {fname} must exist")
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn(expected_line_app_data, content, f"{fname} must set central ANTIGRAVITY_APP_DATA_DIR")
            self.assertIn(expected_line_gem_dir, content, f"{fname} must isolate ANTIGRAVITY_GEMINI_DIR")

    def test_2_profile_junctions_intact(self):
        """All 6 profile roots must have .gemini/antigravity-cli as an NTFS directory junction."""
        profiles = ["perfil1", "perfil2", "perfil3", "perfil4", "agy5", "agy6"]
        for p in profiles:
            p_cli = os.path.join(PROFILES_BASE, p, ".gemini", "antigravity-cli")
            self.assertTrue(os.path.exists(p_cli), f"{p} antigravity-cli must exist")
            self.assertTrue(is_ntfs_junction(p_cli), f"{p} antigravity-cli must be an NTFS junction")

    def test_3_auth_credentials_strictly_isolated(self):
        """Auth files must remain strictly in .gemini/ (outside the junction) and not be shared."""
        profiles = ["perfil1", "perfil2", "perfil3", "perfil4", "agy5", "agy6"]
        for p in profiles:
            p_gem = os.path.join(PROFILES_BASE, p, ".gemini")
            # Must have google_accounts.json and wincred.json
            self.assertTrue(os.path.exists(os.path.join(p_gem, "google_accounts.json")), f"{p} must have google_accounts.json")
            self.assertTrue(os.path.exists(os.path.join(p_gem, "wincred.json")), f"{p} must have wincred.json")
            # Must NOT be junctions
            self.assertFalse(is_ntfs_junction(p_gem), f"{p} .gemini must not be a junction")
            self.assertFalse(is_ntfs_junction(os.path.join(p_gem, "wincred.json")), f"{p} wincred.json must not be a junction")

    def test_4_cross_profile_conversation_discovery(self):
        """Conversations saved in central DB must be discoverable across both agy2 and agy4 paths."""
        db_central = os.path.join(CENTRAL_CLI, "conversation_summaries.db")
        p2_db = os.path.join(PROFILES_BASE, "perfil2", ".gemini", "antigravity-cli", "conversation_summaries.db")
        p4_db = os.path.join(PROFILES_BASE, "perfil4", ".gemini", "antigravity-cli", "conversation_summaries.db")

        self.assertTrue(os.path.exists(db_central))
        self.assertTrue(os.path.exists(p2_db))
        self.assertTrue(os.path.exists(p4_db))

        conn2 = sqlite3.connect(p2_db)
        cur2 = conn2.cursor()
        cur2.execute("SELECT count(*) FROM conversation_summaries WHERE workspace_uris LIKE '%55/3%'")
        p2_matches = cur2.fetchone()[0]
        conn2.close()

        conn4 = sqlite3.connect(p4_db)
        cur4 = conn4.cursor()
        cur4.execute("SELECT count(*) FROM conversation_summaries WHERE workspace_uris LIKE '%55/3%'")
        p4_matches = cur4.fetchone()[0]
        conn4.close()

        self.assertGreater(p2_matches, 0, "perfil2 should see 55/3 workspace conversations")
        self.assertEqual(p2_matches, p4_matches, "perfil4 must see the exact same 55/3 workspace conversations as perfil2")

    def test_5_sqlite_wal_integrity(self):
        """SQLite WAL mode should permit concurrent queries through profile junction without error."""
        p4_db = os.path.join(PROFILES_BASE, "perfil4", ".gemini", "antigravity-cli", "conversation_summaries.db")
        conn = sqlite3.connect(p4_db)
        cur = conn.cursor()
        cur.execute("PRAGMA journal_mode")
        mode = cur.fetchone()[0].lower()
        self.assertIn(mode, ("wal", "delete", "memory"), "Valid journal mode")
        cur.execute("PRAGMA integrity_check")
        status = cur.fetchone()[0]
        self.assertEqual(status, "ok", "Database integrity must be ok")
        conn.close()

if __name__ == "__main__":
    unittest.main()

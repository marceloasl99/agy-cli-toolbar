import importlib.util
import json
import os
import shutil
import tempfile
import unittest


class TestProfileIsolation(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="agy_test_")
        self.fake_home = os.path.join(self.tmpdir, "home")
        self.fake_local = os.path.join(self.fake_home, "AppData", "Local")
        os.makedirs(os.path.join(self.fake_local, "agy", "bin"), exist_ok=True)
        os.makedirs(os.path.join(self.fake_home, ".agy-perfis"), exist_ok=True)

        self._orig_env = {}
        for k in ("USERPROFILE", "HOME", "LOCALAPPDATA", "AGY_NO_PICKER", "AGY_LAUNCH_DRY_RUN"):
            self._orig_env[k] = os.environ.get(k)

        os.environ["USERPROFILE"] = self.fake_home
        os.environ["HOME"] = self.fake_home
        os.environ["LOCALAPPDATA"] = self.fake_local
        os.environ["AGY_NO_PICKER"] = "1"
        os.environ.pop("AGY_LAUNCH_DRY_RUN", None)

        pm_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "profile_manager.py"))
        spec = importlib.util.spec_from_file_location("pm_test_mod", pm_path)
        self.pm = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.pm)

        # In-memory fake credential store (never touches real Windows Credential Manager)
        self.fake_store = {}

        def fake_read(target="gemini:antigravity"):
            return self.fake_store.get(target)

        def fake_write(data, target="gemini:antigravity"):
            self.fake_store[target] = dict(data)
            return True

        def fake_delete(target="gemini:antigravity"):
            self.fake_store.pop(target, None)
            return True

        self.pm.read_wincred = fake_read
        self.pm.write_wincred = fake_write
        self.pm.delete_wincred = fake_delete

    def tearDown(self):
        for k, v in self._orig_env.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _create_prof_files(self, name, email, token="tok_123", identity=None):
        gdir = os.path.join(self.fake_home, ".agy-perfis", name, ".gemini")
        os.makedirs(gdir, exist_ok=True)
        if email is not None:
            with open(os.path.join(gdir, "wincred.json"), "w", encoding="utf-8") as f:
                json.dump({"token": token, "auth_method": "oauth", "id_token_email": email}, f)
            with open(os.path.join(gdir, "google_accounts.json"), "w", encoding="utf-8") as f:
                json.dump({"active": email, "old": []}, f)
        if identity is not None:
            with open(os.path.join(gdir, self.pm.IDENTITY_FILE), "w", encoding="utf-8") as f:
                json.dump({"email": identity, "bound_at": "2026-01-01T00:00:00"}, f)
        return gdir

    def test_1_pre_run_swaps_to_target_without_touching_other_profile(self):
        p2_dir = self._create_prof_files("perfil2", "p2@example.com", token="tok_p2", identity="p2@example.com")
        self._create_prof_files("agy5", "a5@example.com", token="tok_a5", identity="a5@example.com")

        self.fake_store["gemini:antigravity"] = {
            "token": "tok_p2",
            "auth_method": "oauth",
            "id_token_email": "p2@example.com",
        }
        with open(os.path.join(p2_dir, "wincred.json"), "r", encoding="utf-8") as f:
            p2_before = f.read()

        self.pm.pre_run("agy5")

        self.assertEqual(self.fake_store["gemini:antigravity"]["id_token_email"], "a5@example.com")
        self.assertEqual(self.fake_store["gemini:antigravity"]["token"], "tok_a5")
        with open(os.path.join(p2_dir, "wincred.json"), "r", encoding="utf-8") as f:
            p2_after = f.read()
        self.assertEqual(p2_before, p2_after)

    def test_2_post_run_rejects_mismatched_identity(self):
        p1_dir = self._create_prof_files("perfil1", "a@x.com", token="tok_a", identity="a@x.com")
        self._create_prof_files("perfil2", "b@x.com", token="tok_b", identity="b@x.com")
        with open(os.path.join(p1_dir, "wincred.json"), "r", encoding="utf-8") as f:
            p1_before = f.read()

        self.fake_store["gemini:antigravity"] = {
            "token": "tok_b",
            "auth_method": "oauth",
            "id_token_email": "b@x.com",
        }

        self.pm.post_run("perfil1")

        with open(os.path.join(p1_dir, "wincred.json"), "r", encoding="utf-8") as f:
            p1_after = f.read()
        self.assertEqual(p1_before, p1_after)
        with open(os.path.join(p1_dir, "google_accounts.json"), "r", encoding="utf-8") as f:
            acc = json.load(f)
        self.assertEqual(acc["active"], "a@x.com")

    def test_3_new_profile_first_login_binds_identity(self):
        self.fake_store["gemini:antigravity"] = {
            "token": "old_tok",
            "auth_method": "oauth",
            "id_token_email": "old@x.com",
        }

        self.pm.pre_run("agy7")
        self.assertNotIn("gemini:antigravity", self.fake_store)

        # Simulate user completing login during agy7 session
        self.fake_store["gemini:antigravity"] = {
            "token": "tok_c",
            "auth_method": "oauth",
            "id_token_email": "c@x.com",
        }
        self.pm.post_run("agy7")

        gdir = os.path.join(self.fake_home, ".agy-perfis", "agy7", ".gemini")
        with open(os.path.join(gdir, "wincred.json"), "r", encoding="utf-8") as f:
            wcred = json.load(f)
        with open(os.path.join(gdir, self.pm.IDENTITY_FILE), "r", encoding="utf-8") as f:
            ident = json.load(f)
        self.assertEqual(wcred["id_token_email"], "c@x.com")
        self.assertEqual(ident["email"], "c@x.com")

    def test_4_contaminated_file_quarantined_and_store_deleted(self):
        gdir = self._create_prof_files("perfil3", "b@x.com", token="tok_b", identity="a@x.com")
        self.fake_store["gemini:antigravity"] = {
            "token": "stale",
            "auth_method": "oauth",
            "id_token_email": "stale@x.com",
        }

        self.pm.pre_run("perfil3")

        self.assertFalse(os.path.exists(os.path.join(gdir, "wincred.json")))
        quarantined = [f for f in os.listdir(gdir) if f.startswith("wincred.json.quarantine-")]
        self.assertEqual(len(quarantined), 1)
        self.assertNotIn("gemini:antigravity", self.fake_store)

    def test_5_build_agy_args_and_write_launch_file(self):
        self.assertEqual(self.pm.build_agy_args("all", []), ["--dangerously-skip-permissions"])
        self.assertEqual(self.pm.build_agy_args("all", ["--mode", "plan"]), [])

        workdir = os.path.join(self.tmpdir, "proj")
        os.makedirs(workdir, exist_ok=True)
        lfile = os.path.join(self.tmpdir, "launch.cmd")
        self.pm.write_launch_file(lfile, workdir, ["--dangerously-skip-permissions"])

        with open(lfile, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        self.assertIn(f'cd /d "{workdir}"', content)
        self.assertIn('set "AGY_LAUNCH_ARGS=--dangerously-skip-permissions"', content)

    def test_6_generate_launcher_content(self):
        prof_dir = os.path.join(self.fake_home, ".agy-perfis", "agy5")
        content = self.pm.generate_launcher_content("agy5", prof_dir)
        self.assertIn("pre-run agy5", content)
        self.assertIn("post-run agy5", content)
        self.assertIn("if errorlevel 3", content)
        self.assertIn("%AGY_LAUNCH_ARGS%", content)


if __name__ == "__main__":
    unittest.main()

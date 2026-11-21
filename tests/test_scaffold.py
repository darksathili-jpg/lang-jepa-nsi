from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class ScaffoldTests(unittest.TestCase):
    def test_assets_exist(self):
        for name in ("index.html", "style.css", "app.js"):
            self.assertTrue((ROOT / "app" / name).is_file())

    def test_no_remote_assets(self):
        html = (ROOT / "app" / "index.html").read_text(encoding="utf-8")
        self.assertNotIn("https://", html)
        self.assertNotIn("http://", html)

    def test_no_fake_ai(self):
        js = (ROOT / "app" / "app.js").read_text(encoding="utf-8")
        self.assertIn("aucun checkpoint LANG-JEPA", js)

if __name__ == "__main__":
    unittest.main()

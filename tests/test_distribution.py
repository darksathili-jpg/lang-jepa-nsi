import contextlib
import hashlib
import io
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from distribution.instance import LOCK
from distribution.instance import lock
from distribution.jobs import stop_waiter
from distribution.transfer import extract_zip, fetch
from p5.orchestration import open_experiment
from tutor.engine import LlamaEngine


class ShutdownTests(unittest.TestCase):
    @unittest.skipUnless(hasattr(os, "pidfd_open"), "Descripteur de processus Linux requis.")
    def test_stop_waiter_waits_for_actual_exit(self):
        with subprocess.Popen([sys.executable, "-c", "import time; time.sleep(30)"]) as process:
            try:
                with stop_waiter(process.pid) as wait:
                    with self.assertRaisesRegex(ValueError, "sortie du serveur"):
                        wait(0)
                    process.terminate()
                    wait(5)
                    self.assertIsNotNone(process.poll())
            finally:
                if process.poll() is None:
                    process.kill()


class Response(io.BytesIO):
    def __init__(self, data, status=200, headers=None):
        super().__init__(data)
        self.status = status
        self.headers = headers or {}

    def geturl(self):
        return "https://source.example/demo"


class TransferTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.path = Path(self.tmp.name) / "demo"
        self.part = self.path.with_suffix(".part")
        self.payload = b"abcdefgh"
        self.meta = {"sha256": hashlib.sha256(self.payload).hexdigest(), "bytes": len(self.payload)}

    def test_resume_only_if_exact_range(self):
        self.part.write_bytes(self.payload[:3])
        with patch("distribution.transfer.urllib.request.urlopen",
                   return_value=Response(self.payload[3:], 206, {"Content-Range": "bytes 3-7/8"})) as download:
            fetch("https://source.example/demo", self.path, self.meta)
        self.assertEqual(download.call_args.args[0].get_header("Range"), "bytes=3-")
        self.assertEqual(self.path.read_bytes(), self.payload)
        self.assertFalse(self.part.exists())

    def test_ignoring_range_start_again_and_reuse_without_network(self):
        self.part.write_bytes(b"xy")
        with patch("distribution.transfer.urllib.request.urlopen", return_value=Response(self.payload)):
            fetch("https://source.example/demo", self.path, self.meta)
        with patch("distribution.transfer.urllib.request.urlopen", side_effect=AssertionError("hors ligne")):
            fetch("https://source.example/demo", self.path, self.meta)
        self.assertEqual(self.path.read_bytes(), self.payload)

    def test_truncated_response_remains_partial(self):
        with patch("distribution.transfer.urllib.request.urlopen", return_value=Response(self.payload[:3])):
            with self.assertRaisesRegex(ValueError, "incomplet"):
                fetch("https://source.example/demo", self.path, self.meta)
        self.assertEqual(self.part.read_bytes(), self.payload[:3])
        self.assertFalse(self.path.exists())

    def test_bad_checksum_removes_partial_and_preserves_existing_file(self):
        with patch("distribution.transfer.urllib.request.urlopen", return_value=Response(b"x" * 8)):
            with self.assertRaisesRegex(ValueError, "Empreinte"):
                fetch("https://source.example/demo", self.path, self.meta)
        self.assertFalse(self.part.exists())
        self.path.write_bytes(b"conserver")
        with self.assertRaises(ValueError):
            fetch("https://source.example/demo", self.path, self.meta)
        self.assertEqual(self.path.read_bytes(), b"conserver")

    def test_traversal_archive_is_rejected(self):
        with zipfile.ZipFile(self.path, "w") as archive:
            archive.writestr("../sortie", self.payload)
        with self.assertRaisesRegex(ValueError, "Entrée ZIP"):
            extract_zip(self.path, self.path.parent / "runtime")

    def test_lock_refuses_parallel_operation(self):
        with lock(self.path), contextlib.ExitStack() as nested:
            with self.assertRaisesRegex(ValueError, "déjà en cours"):
                nested.enter_context(lock(self.path))
        with lock(self.path):
            self.assertTrue(self.path.is_file())

    def test_partial_weights_are_distinct_from_absence(self):
        self.assertEqual(LlamaEngine(self.path.parent, "smol", 2).status()["state"], "absent")
        self.part.write_bytes(self.payload[:3])
        self.assertEqual(LlamaEngine(self.path.parent, "smol", 2).status()["state"], "incomplete")

    def test_installed_profile_must_match_the_p5_recipe(self):
        try:
            from p5.jepa import save, train
        except ModuleNotFoundError:
            self.skipTest("NumPy est requis pour ce contrôle de profil.")
        from p5.data import load_corpus

        rows = [row for row in load_corpus() if row.partage == "train"][:5]
        model, _ = train(rows, "fixe-24", 11, 1)
        save(model, self.path, {"graine": 11})
        self.assertEqual(open_experiment("c", self.path).status()["state"], "ready")
        result = open_experiment("c", self.path, recipe=LOCK["jepa"]).status()
        self.assertEqual(result["state"], "incompatible")
        self.assertTrue(result["checks"]["integrite"])
        self.assertFalse(result["checks"]["prediction"])

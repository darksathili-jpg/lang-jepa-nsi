"""Contrôles de préparation, indépendants de PyTorch et des poids du modèle."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from scripts import lang_jepa_cpu as cpu


class CpuPreparationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.bundle = Path(temporary.name)
        self.revision = "test-local"
        source_digest = self.write_file("upstream.tar.gz", b"archive de test")
        encoder_digest = self.write_file("encoder.pth", b"fichier de test encodeur")
        decoder_digest = self.write_file("decoder.pt", b"fichier de test decodeur")
        config_digest = self.write_file("encoder_config.yaml", b"configuration de test")
        self.lock = {
            "revision": self.revision,
            "roberta_revision": "test-tokenizer",
            "files": {"upstream.tar.gz": {"sha256": source_digest}},
        }
        self.manifest = {
            "upstream_revision": self.revision,
            "encoder": {
                "provenance": "Test de verification de fichiers",
                "sha256": encoder_digest,
                "encoder_config_sha256": config_digest,
            },
            "decoder": {
                "provenance": "Test de verification de fichiers",
                "sha256": decoder_digest,
                "encoder_sha256": encoder_digest,
            },
        }
        (self.bundle / "p2").mkdir()
        (self.bundle / "p2" / "upstream.json").write_text(json.dumps(self.lock), encoding="utf-8")
        self.save_manifest()
        patcher = patch.object(cpu, "ROOT", self.bundle)
        patcher.start()
        self.addCleanup(patcher.stop)

    def write_file(self, name, data):
        (self.bundle / name).write_bytes(data)
        return hashlib.sha256(data).hexdigest()

    def save_manifest(self):
        (self.bundle / "checkpoints.json").write_text(
            json.dumps(self.manifest), encoding="utf-8-sig"
        )

    def test_encoder_mode_does_not_require_decoder(self):
        (self.bundle / "decoder.pt").unlink()
        verified = cpu.verify_assets(self.bundle, decode=False)
        self.assertEqual(verified["sha256"]["encoder.pth"], self.manifest["encoder"]["sha256"])
        self.assertNotIn("decoder.pt", verified["sha256"])

    def test_decoder_mode_requires_decoder(self):
        verified = cpu.verify_assets(self.bundle, decode=True)
        self.assertEqual(verified["sha256"]["decoder.pt"], self.manifest["decoder"]["sha256"])
        (self.bundle / "decoder.pt").unlink()
        with self.assertRaisesRegex(FileNotFoundError, "décodeur absent"):
            cpu.verify_assets(self.bundle, decode=True)

    def test_decoder_must_reference_the_encoder_used_for_training(self):
        self.manifest["decoder"]["encoder_sha256"] = "0" * 64
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "autre checkpoint"):
            cpu.verify_assets(self.bundle, decode=True)

    def test_wrong_upstream_revision_is_rejected(self):
        self.manifest["upstream_revision"] = "another-revision"
        self.save_manifest()
        with self.assertRaisesRegex(ValueError, "révision"):
            cpu.verify_assets(self.bundle, decode=False)

    def test_corrupted_weights_are_rejected(self):
        self.write_file("encoder.pth", b"corrompu")
        with self.assertRaisesRegex(ValueError, "Empreinte SHA-256 différente"):
            cpu.verify_assets(self.bundle, decode=False)

    def test_missing_checkpoint_does_not_emit_a_report(self):
        (self.bundle / "encoder.pth").unlink()
        output = self.bundle / "result.json"
        text = self.bundle / "probe.txt"
        text.write_text("Une phrase.", encoding="utf-8")
        command = [
            sys.executable, "-S", "-X", "utf8", str(Path(cpu.__file__).resolve()),
            "--bundle", str(self.bundle), "--input", str(text), "--output", str(output),
        ]
        run = subprocess.run(command, capture_output=True, encoding="utf-8", check=False)
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertIn("aucun checkpoint LANG-JEPA", run.stderr)
        self.assertEqual(run.stdout, "")
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()

import json
import unittest

from tutor.catalog import ROOT


REFERENCE = json.loads((ROOT / "p4/reference.json").read_text(encoding="utf-8"))


class RegressionEvidenceTests(unittest.TestCase):
    def test_original_model_repeated_question_after_causal_explanation(self):
        rows = [json.loads(line) for line in (ROOT / "p4/preuves/avant.jsonl").read_text(
            encoding="utf-8").splitlines()]
        self.assertEqual([row["learner"] for row in rows], REFERENCE)
        self.assertEqual(rows[1]["answer"]["question"], rows[3]["answer"]["question"])
        self.assertEqual(rows[1]["answer"]["stage"], rows[3]["answer"]["stage"])
        self.assertIn("valeur de `m`", rows[3]["answer"]["question"])
        self.assertEqual(rows[3]["raw"]["finish"], "stop")


if __name__ == "__main__":
    unittest.main()

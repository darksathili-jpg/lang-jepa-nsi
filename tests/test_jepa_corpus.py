import unittest

from evaluation.corpus import load_corpus, make_pairs
from evaluation.metrics import lexical_cosine, lexical_reference, rank, summarize
from pedagogy.catalogue import EXERCISES, for_level, validate_catalogue


class CorpusTests(unittest.TestCase):
    def test_splits_are_disjoint(self):
        docs = load_corpus()
        train, test = (make_pairs(docs, split) for split in ("train", "test"))
        self.assertEqual((len(train), len(test)), (24, 24))
        self.assertFalse({item.document for item in train} & {item.document for item in test})
        for pair in train + test:
            self.assertTrue(pair.context)
            self.assertNotIn(pair.target, pair.context)

    def test_catalogue_keeps_solutions_out_of_public_exercise_list(self):
        validate_catalogue()
        self.assertEqual(len(EXERCISES), 4)
        self.assertEqual([row["id"] for row in for_level("terminale")], ["recursivite-base"])
        for exercise in for_level("premiere") + for_level("terminale"):
            self.assertFalse({"hints", "tests", "error"} & exercise.keys())
        self.assertEqual(EXERCISES["maximum"]["tests"][-1]["contract"], "hors précondition")

    def test_lexical_reference_and_ties(self):
        vector = lexical_reference(["boucle bornée", "clé du dictionnaire"])
        self.assertEqual(lexical_cosine(vector("boucle"), vector("BOUCLE")), 1)
        self.assertEqual(vector("jamais vu"), {})
        row = rank({"z": 0, "a": 0, "b": 1}, {"z"})
        self.assertEqual(row["order"], ["b", "a", "z"])
        self.assertEqual(summarize([row]), {"count": 1, "top1": 0.0, "mrr": 1/3})


if __name__ == "__main__":
    unittest.main()

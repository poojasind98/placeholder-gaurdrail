import csv
import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import torch
from eval import evalModel, parse_prediction
from customDataset import CustomDataset


class EvaluationTests(unittest.TestCase):
    def test_limit_keeps_sequences_and_labels_aligned(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "input.csv"
            with path.open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["Content", "Label"])
                writer.writerows([("service started ;-; service stopped", 0),
                                 ("error", 1), ("ignored", 0)])
            dataset = CustomDataset(path, max_samples=2)
            self.assertEqual(len(dataset), 2)
            self.assertEqual(list(dataset.get_label()), [0, 1])
            self.assertEqual(list(dataset[0][0]), ["service started", "service stopped"])

    def test_case_and_word_boundaries(self):
        self.assertEqual(parse_prediction("The sequence is ANOMALOUS."), 1)
        self.assertEqual(parse_prediction("normal."), 0)
        for text in ("abnormal", "unclassified", ""):
            with self.assertRaises(ValueError):
                parse_prediction(text)

    def test_predictions_metrics_and_export_agree(self):
        class Model:
            device = "cpu"
            Llama_tokenizer = SimpleNamespace(
                batch_decode=lambda ids, **kwargs: ["normal", "ANOMALOUS", "normal"])

            def eval(self):
                pass

            def __call__(self, inputs, positions):
                return torch.zeros(3, 1, dtype=torch.long)

        class Loader:
            dataset = SimpleNamespace(get_label=lambda: np.array([0, 1, 1]))

            def __iter__(self):
                yield {"inputs": torch.zeros(3, 1), "seq_positions": torch.tensor([1, 2])}

        with tempfile.TemporaryDirectory() as tmp:
            metrics = evalModel(Model(), Loader(), output_dir=tmp)
            self.assertEqual(metrics["samples"], 3)
            self.assertAlmostEqual(metrics["accuracy"], 2 / 3)
            self.assertEqual(metrics["precision"], 1)
            self.assertEqual(metrics["recall"], 0.5)
            self.assertAlmostEqual(metrics["f1"], 2 / 3)
            self.assertEqual(json.loads((Path(tmp) / "metrics.json").read_text()), metrics)
            with (Path(tmp) / "predictions.csv").open() as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual([row["prediction"] for row in rows], ["0", "1", "0"])


if __name__ == "__main__":
    unittest.main()

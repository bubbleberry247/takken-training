import csv
import copy
import importlib.util
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_builder():
    path = ROOT / "tools" / "build_takken_import_csv.py"
    spec = importlib.util.spec_from_file_location("takken_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


class TakkenQuestionbankPipelineTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.builder = load_builder()
        cls.source = read_rows(cls.builder.SRC)
        cls.curated = read_rows(cls.builder.DEST)
        cls.generated = [cls.builder.normalize_row(row) for row in cls.source]
        cls.source_by_id = {row["qId"]: row for row in cls.source}
        cls.generated_by_id = {row["qId"]: row for row in cls.generated}

    def test_dataset_cardinality(self):
        self.assertEqual(len(self.generated), 600)
        self.assertEqual(len(self.generated_by_id), 600)

    def test_generated_csv_is_current(self):
        self.assertEqual(self.builder.compare_rows(self.generated, self.curated), [])
        self.builder.validate_dataset(self.curated, "test curated data")

    def test_duplicate_generated_row_is_rejected(self):
        duplicated = self.curated + [copy.deepcopy(self.curated[0])]
        with self.assertRaises(ValueError):
            self.builder.validate_dataset(duplicated, "duplicate test data")

    def test_unexpected_csv_column_is_rejected(self):
        with self.assertRaises(ValueError):
            self.builder.validate_headers(self.builder.HEADERS + ["unexpected"], "schema test")

    def test_structured_question_inventory(self):
        self.assertEqual(len(self.builder.COUNT_QUESTION_IDS), 22)
        self.assertEqual(len(self.builder.COMBINATION_QUESTION_IDS), 4)
        self.builder.validate_structured_questions(self.generated)

    def test_r3_q38_item_labels_and_line_breaks(self):
        for q_id in ("R3atakken-038", "R3btakken-038"):
            with self.subTest(q_id=q_id):
                lines = self.generated_by_id[q_id]["stem"].splitlines()
                self.assertEqual(lines[-4][0], "ア")
                self.assertEqual(lines[-3][0], "イ")
                self.assertEqual(lines[-2][0], "ウ")
                self.assertEqual(lines[-1][0], "エ")
                self.assertTrue(all(line.startswith(label + "\u3000") for line, label in zip(lines[-4:], "アイウエ")))

    def test_structured_question_invariants(self):
        structured = self.builder.COUNT_QUESTION_IDS | self.builder.COMBINATION_QUESTION_IDS
        for q_id in structured:
            with self.subTest(q_id=q_id):
                source = self.source_by_id[q_id]
                generated = self.generated_by_id[q_id]
                self.assertEqual(generated["correct"], source["correct"].upper())
                self.assertEqual(generated["status"], "published")
                self.assertEqual(generated["lawTag"], source["lawTag"].strip())

    def test_structured_question_exact_fixtures(self):
        for q_id, (expected_choices, expected_correct) in self.builder.STRUCTURED_QUESTION_FIXTURES.items():
            with self.subTest(q_id=q_id):
                row = self.generated_by_id[q_id]
                self.assertEqual(tuple(row["choice" + key] for key in "ABCD"), expected_choices)
                self.assertEqual(row["correct"], expected_correct)

    def test_repeated_structured_choices_are_rejected(self):
        mutated = copy.deepcopy(self.generated)
        by_id = {row["qId"]: row for row in mutated}
        for key in "ABCD":
            by_id["R7takken-003"]["choice" + key] = "一つ"
        with self.assertRaises(ValueError):
            self.builder.validate_structured_questions(mutated)

    def test_structured_stem_change_is_rejected(self):
        mutated = copy.deepcopy(self.generated)
        by_id = {row["qId"]: row for row in mutated}
        by_id["R7takken-003"]["stem"] += "改変"
        with self.assertRaises(ValueError):
            self.builder.validate_structured_questions(mutated)

    def test_structured_stem_crlf_is_portable(self):
        crlf_rows = copy.deepcopy(self.generated)
        for row in crlf_rows:
            canonical = row["stem"].replace("\r\n", "\n").replace("\r", "\n")
            row["stem"] = canonical.replace("\n", "\r\n")
        self.builder.validate_structured_questions(crlf_rows)

    def test_structured_choice_e_is_rejected(self):
        mutated = copy.deepcopy(self.generated)
        by_id = {row["qId"]: row for row in mutated}
        by_id["R7takken-003"]["choiceE"] = "五つ"
        with self.assertRaises(ValueError):
            self.builder.validate_structured_questions(mutated)

    def test_none_answer_options_are_preserved(self):
        for q_id in ("R6takken-006", "R6takken-041", "R7takken-028", "R7takken-040"):
            with self.subTest(q_id=q_id):
                self.assertEqual(self.generated_by_id[q_id]["choiceD"], "なし")


if __name__ == "__main__":
    unittest.main()

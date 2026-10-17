import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "sas_log_check.py"
spec = importlib.util.spec_from_file_location("sas_log_check", SCRIPT)
checker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checker)


class SasLogCheckerTests(unittest.TestCase):
    def run_cli(self, folder, *options):
        return subprocess.run([sys.executable, str(SCRIPT), str(folder), *options],
                              capture_output=True, text=True)

    def test_messages_source_lines_and_recursive_uppercase_extension(self):
        with tempfile.TemporaryDirectory(prefix="sas logs ") as folder:
            root = Path(folder)
            (root / "one.log").write_text(
                '\ufeff  ERROR 180-322: Invalid statement.\n'
                'WARNING: Variable is uninitialized.\nNOTE: Read 2 records.\n'
                '123 put "ERROR: example";\nordinary text with WARNING: inside\n', encoding="utf-8")
            (root / "sub").mkdir()
            (root / "sub/two.LOG").write_text("note: Nested note.\n", encoding="utf-8")
            (root / "ignored.txt").write_text("ERROR: Not a log.\n")
            report = checker.scan(root)
            self.assertEqual(report["files_scanned"], 1)
            self.assertEqual(report["counts"], {"ERROR": 1, "WARNING": 1, "NOTE": 1})
            self.assertEqual(report["findings"][0]["line"], 1)
            result = self.run_cli(root, "-r", "--format", "json")
            self.assertEqual(result.returncode, 1)
            report = json.loads(result.stdout)
            self.assertEqual(report["files_scanned"], 2)
            self.assertEqual(report["counts"]["NOTE"], 2)

    def test_failure_thresholds(self):
        with tempfile.TemporaryDirectory() as folder:
            log = Path(folder) / "a.log"
            for message, expected in [
                ("NOTE: done", [0, 0, 1, 0]),
                ("WARNING: check", [0, 1, 1, 0]),
                ("ERROR: failed", [1, 1, 1, 0]),
                ("all clear", [0, 0, 0, 0]),
            ]:
                log.write_text(message)
                for threshold, code in zip(("error", "warning", "note", "none"), expected):
                    with self.subTest(message=message, threshold=threshold):
                        self.assertEqual(self.run_cli(folder, "--fail-on", threshold).returncode, code)

    def test_empty_missing_and_decoding_failures(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(self.run_cli(folder).returncode, 2)
            self.assertEqual(self.run_cli(Path(folder) / "missing").returncode, 2)
            (Path(folder) / "legacy.log").write_bytes(b"WARNING: caf\xe9\n")
            result = self.run_cli(folder, "--format", "json", "--fail-on", "none")
            self.assertEqual(result.returncode, 2)
            self.assertTrue(json.loads(result.stdout)["scan_errors"])
            self.assertEqual(self.run_cli(folder, "--encoding", "latin-1").returncode, 0)
            self.assertEqual(self.run_cli(folder, "--encoding", "invalid-encoding").returncode, 2)

    def test_unreadable_log_is_reported(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / "a.log").touch()
            with patch.object(Path, "open", side_effect=PermissionError("access denied")):
                report = checker.scan(folder)
            self.assertEqual(len(report["scan_errors"]), 1)


if __name__ == "__main__":
    unittest.main()

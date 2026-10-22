import argparse
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

FILE = Path(__file__).resolve().parent / "acceptance/run.py"
spec = importlib.util.spec_from_file_location("acceptance_run", FILE)
driver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(driver)


class RecordTests(unittest.TestCase):
    def test_records_distinguish_execution_static_and_blocked(self):
        with tempfile.TemporaryDirectory() as temp:
            payload = Path(temp) / "input.json"
            payload.write_text("{}")
            args = argparse.Namespace(directory=Path(temp), mode="static", graph_id="sample",
                evidence_kind="static", relocate=False, input=payload, resume=None, server=None)
            with patch.object(driver, "static_probe", return_value={"ok": True}):
                self.assertEqual(driver.record_run(args)["outcome"], "static-passed")
                args.mode, args.evidence_kind = "python", "double"
                with patch.object(driver, "python_probe", side_effect=ModuleNotFoundError("langgraph")):
                    record = driver.record_run(args)
                    self.assertEqual(record["outcome"], "blocked")
                    self.assertEqual(record["evidence_kind"], "double")
                    self.assertEqual(record["judgement"], "pending-review")
                with patch.object(driver, "python_probe"):
                    self.assertEqual(driver.record_run(args)["outcome"], "executed")
                with patch.object(driver, "python_probe", side_effect=ValueError("bad graph")):
                    self.assertEqual(driver.record_run(args)["outcome"], "failed")

    def test_relocation_uses_new_directory_with_resources(self):
        with tempfile.TemporaryDirectory() as temp:
            app = Path(temp) / "app"
            app.mkdir()
            (app / "resource").write_text("template")
            args = argparse.Namespace(directory=app, mode="static", graph_id="sample",
                evidence_kind="static", relocate=True, input=None, resume=None, server=None)
            def inspect_moved(path):
                self.assertNotEqual(path, app)
                self.assertEqual((path / "resource").read_text(), "template")
                return {"ok": True}
            with patch.object(driver, "static_probe", side_effect=inspect_moved):
                self.assertEqual(driver.record_run(args)["outcome"], "static-passed")


if __name__ == "__main__":
    unittest.main()

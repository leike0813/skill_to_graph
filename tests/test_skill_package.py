import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skill-to-graph/scripts/skill_package.py"


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.source = self.work / "sample"
        self.source.mkdir()
        (self.source / "SKILL.md").write_text("---\nname: sample\ndescription: Test package\ndisable-model-invocation: true\n---\nUse templates.\n", encoding="utf-8")
        (self.source / "templates").mkdir()
        (self.source / "templates/data.bin").write_bytes(b"\x00\xff")
        script = self.source / "run.sh"
        script.write_text("#!/bin/sh\nexit 0\n")
        script.chmod(0o755)

    def call(self, *args):
        result = subprocess.run([sys.executable, str(SCRIPT), *map(str, args)], cwd=self.work,
                                text=True, capture_output=True)
        self.assertFalse(result.stderr, result.stderr)
        data = json.loads(result.stdout)
        self.assertEqual(set(data), {"ok", "operation", "data", "issues"})
        self.assertIsInstance(data["data"], dict)
        self.assertEqual(data["ok"], result.returncode == 0)
        return result.returncode, data

    def test_inspect_arbitrary_resource_directory_and_platform_field(self):
        status, report = self.call("inspect", self.source)
        self.assertEqual(status, 0)
        self.assertTrue(report["data"]["metadata"]["disable-model-invocation"])
        self.assertIn({"path": "templates/data.bin", "type": "file"}, report["data"]["files"])

    def test_invalid_metadata(self):
        for header in ("name: sample\ndescription: ''", "name: Sample\ndescription: x",
                       "name: other\ndescription: x", "name: sample\ndescription: x\nmetadata: {count: 1}",
                       "!!python/object:os.system {}", "[invalid",
                       "name: sample\ndescription: x\nextra: &loop [*loop]"):
            with self.subTest(header=header):
                (self.source / "SKILL.md").write_text(f"---\n{header}\n---\n")
                status, report = self.call("inspect", self.source)
                self.assertEqual(status, 3)
                self.assertEqual(report["issues"][0]["code"], "invalid-source")

    def test_copy_default_explicit_and_materialized_links(self):
        (self.source / "link").symlink_to("templates/data.bin")
        for args, target in (((), self.work / "sample-graph"),
                             (("--output", "custom"), self.work / "custom")):
            with self.subTest(target=target):
                status, result = self.call("copy", self.source, *args)
                self.assertEqual(status, 0, result)
                snapshot = target / "source/sample"
                self.assertEqual((snapshot / "templates/data.bin").read_bytes(), b"\x00\xff")
                self.assertEqual((snapshot / "run.sh").stat().st_mode & 0o777, 0o755)
                self.assertEqual((snapshot / "link").read_bytes(), b"\x00\xff")
                self.assertFalse((snapshot / "link").is_symlink())
        self.assertTrue((self.source / "link").is_symlink())

    def test_conflicts_never_overwrite(self):
        existing = self.work / "existing"
        existing.mkdir()
        (existing / "keep").write_text("mine")
        for destination in (existing, self.work / "unused/../existing", self.source, self.source / "nested", self.work):
            with self.subTest(destination=destination):
                status, result = self.call("copy", self.source, "--output", destination)
                self.assertEqual(status, 4)
                self.assertEqual(result["issues"][0]["code"], "output-conflict")
        self.assertEqual((existing / "keep").read_text(), "mine")
        self.assertFalse((self.source / "nested").exists())
        self.assertFalse((self.work / "unused").exists())
        self.assertEqual((self.source / "templates/data.bin").read_bytes(), b"\x00\xff")

    def test_errors_and_help_are_process_contracts(self):
        for args, status, code in (((), 2, "invalid-argument"), (("unknown",), 2, "invalid-argument"),
                                   (("inspect", "missing"), 3, "invalid-source"),
                                   (("copy", self.source, "--unknown"), 2, "invalid-argument")):
            actual, report = self.call(*args)
            self.assertEqual(actual, status)
            self.assertEqual(report["issues"][0]["code"], code)
        for args in (("--help",), ("copy", "--help")):
            result = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=self.work, capture_output=True)
            self.assertEqual(result.returncode, 0)
            self.assertIn(b"usage:", result.stdout)
        self.assertFalse((self.work / "sample-graph").exists())

    def test_unreadable_content_is_not_success(self):
        (self.source / "broken").symlink_to("absent")
        status, report = self.call("inspect", self.source)
        self.assertEqual(status, 5)
        self.assertEqual(report["issues"][0]["code"], "io-error")


if __name__ == "__main__":
    unittest.main()

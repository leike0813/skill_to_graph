import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / "skill-to-graph/scripts/check_graph.py"


class CheckGraphTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.work = Path(self.temp.name)
        self.app = self.work / "app"
        (self.app / "skill_graph").mkdir(parents=True)
        (self.app / "skill_graph/__init__.py").write_text("", encoding="utf-8")
        (self.app / "skill_graph/graph.py").write_text(
            "from pathlib import Path\n"
            "Path(__file__).with_name('executed').write_text('imported')\n"
            "from dependency_not_installed import agent\n"
            "raise RuntimeError('must not be imported')\n",
            encoding="utf-8",
        )
        (self.app / ".env").write_text("", encoding="utf-8")
        legacy = self.app / "source/original/scripts/legacy.py"
        legacy.parent.mkdir(parents=True)
        legacy.write_text('print "Python 2 source snapshot"\n', encoding="utf-8")
        self.set_config({
            "dependencies": ["."],
            "graphs": {"sample": "./skill_graph/graph.py:graph"},
            "env": ".env",
        })

    def set_config(self, config):
        (self.app / "langgraph.json").write_text(json.dumps(config), encoding="utf-8")

    def call(self, *args):
        result = subprocess.run(
            [sys.executable, str(SCRIPT), *map(str, args)],
            cwd=self.work,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.stderr, "", result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(set(report), {"ok", "operation", "data", "issues"})
        self.assertEqual(report["operation"], "check")
        self.assertEqual(report["ok"], result.returncode == 0)
        return result.returncode, report

    def test_valid_file_entry_is_static_and_skips_source_snapshot(self):
        status, report = self.call(self.app)
        self.assertEqual(status, 0, report)
        self.assertEqual(report["issues"], [])
        self.assertEqual(report["data"]["checked_files"], [
            "langgraph.json", "skill_graph/__init__.py", "skill_graph/graph.py",
        ])
        self.assertEqual(report["data"]["graph_entries"], {
            "sample": "./skill_graph/graph.py:graph",
        })
        self.assertEqual(report["data"]["unresolved_entries"], {})
        self.assertFalse((self.app / "skill_graph/executed").exists())

    def test_local_module_entry_and_external_module_entry(self):
        config = {"dependencies": ["."], "graphs": {"local": "skill_graph.graph:graph"}}
        self.set_config(config)
        status, report = self.call(self.app)
        self.assertEqual(status, 0, report)
        self.assertEqual(report["data"]["unresolved_entries"], {})
        config["graphs"] = {"external": "installed_package.graph:graph"}
        self.set_config(config)
        status, report = self.call(self.app)
        self.assertEqual(status, 0, report)
        self.assertEqual(report["data"]["graph_entries"], {"external": "installed_package.graph:graph"})
        self.assertEqual(report["data"]["unresolved_entries"], {
            "graphs.external": "installed_package.graph:graph",
        })

    def test_python_syntax_error(self):
        (self.app / "skill_graph/graph.py").write_text("def broken(:\n", encoding="utf-8")
        status, report = self.call(self.app)
        self.assertEqual(status, 6)
        self.assertEqual(report["issues"][0]["code"], "invalid-artifact")
        self.assertEqual(report["issues"][0]["path"], "skill_graph/graph.py")

    def test_missing_local_entry(self):
        for entry in ("./skill_graph/absent.py:graph", "skill_graph.absent:graph"):
            with self.subTest(entry=entry):
                self.set_config({"dependencies": ["."], "graphs": {"sample": entry}})
                status, report = self.call(self.app)
                self.assertEqual(status, 6)
                self.assertEqual(report["issues"][0]["code"], "invalid-artifact")

    def test_invalid_structure_and_explicit_resources(self):
        cases = [
            ({"graphs": {"sample": "./skill_graph/graph.py:graph"}}, "dependencies"),
            ({"dependencies": ["."], "graphs": {}}, "graphs"),
            ({"dependencies": ["."], "graphs": {"sample": 1}}, "graphs"),
            ({"dependencies": ["./missing"], "graphs": {"sample": "./skill_graph/graph.py:graph"}}, "dependency"),
            ({"dependencies": ["."], "graphs": {"sample": "./skill_graph/graph.py:graph"}, "env": "absent.env"}, "env"),
            ({"dependencies": ["."], "graphs": {"sample": "./skill_graph/graph.py:graph"},
              "auth": {"path": "./missing.py:auth"}}, "auth"),
        ]
        for config, fragment in cases:
            with self.subTest(fragment=fragment):
                self.set_config(config)
                status, report = self.call(self.app)
                self.assertEqual(status, 6)
                issue = report["issues"][0]
                self.assertEqual(issue["code"], "invalid-artifact")
                self.assertIn(fragment, issue["detail"])

        (self.app / "langgraph.json").write_text("{broken", encoding="utf-8")
        status, report = self.call(self.app)
        self.assertEqual(status, 6)
        self.assertEqual(report["issues"][0]["code"], "invalid-artifact")

    def test_help_arguments_and_missing_directory(self):
        before = sorted(path.relative_to(self.app) for path in self.app.rglob("*"))
        result = subprocess.run(
            [sys.executable, str(SCRIPT), "--help"], cwd=self.work, text=True, capture_output=True,
        )
        self.assertEqual(result.returncode, 0)
        help_text = " ".join(result.stdout.split())
        self.assertIn("usage:", help_text.lower())
        self.assertIn("statically unresolvable", help_text)
        self.assertIn("never imported or run", help_text)
        self.assertEqual(before, sorted(path.relative_to(self.app) for path in self.app.rglob("*")))

        for args in ((), (self.app, "extra"), (self.work / "missing",)):
            with self.subTest(args=args):
                status, report = self.call(*args)
                if len(args) == 1 and args[0] == self.work / "missing":
                    self.assertEqual(status, 5)
                    self.assertEqual(report["issues"][0]["code"], "io-error")
                else:
                    self.assertEqual(status, 2)
                    self.assertEqual(report["issues"][0]["code"], "invalid-argument")


if __name__ == "__main__":
    unittest.main()

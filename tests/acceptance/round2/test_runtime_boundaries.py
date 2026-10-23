"""Fast behavior probes for language propagation and source-permitted resubmission."""
import importlib.util
from contextlib import closing
import json
import os
from pathlib import Path
import sqlite3
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("round2_literature_test", ROOT / "generated/literature-analysis-graph/skill_graph/graph.py")
graph = importlib.util.module_from_spec(spec)
spec.loader.exec_module(graph)


class RuntimeBoundaries(unittest.TestCase):
    def test_scoring_input_can_be_corrected_without_changing_locked_form(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            draft = {"form_id": "locked", "paper_type_choices": [{"paper_type": "empirical", "selected": False}],
                     "paper_type_reason": "", "dimension_reviews": [{"dimension_key": "rigor", "name": "Locked name", "summary": ""}],
                     "criterion_reviews": [{"criterion_key": "evidence", "max_score": 5, "score": None}]}
            target = work / "score.json"
            target.write_text(json.dumps(draft))
            locked = work / "scoring_review_form.locked.json"
            locked.write_text(json.dumps(draft))
            decisions = {"paper_type": "empirical", "paper_type_reason": "From paper",
                         "dimension_reviews": {"rigor": {"summary": "Decision"}},
                         "criterion_reviews": [{"criterion_key": "evidence", "score": 3, "max_score": 100}]}

            def agent_factory(*, model, tools, system_prompt):
                tool = next(t for t in tools if t.name == "fill_scoring_draft")

                def invoke(payload, config):
                    rejected = json.loads(tool.invoke({"path": locked.name, "decisions_json": json.dumps(decisions)}))
                    self.assertEqual(rejected["error"], "invalid_scoring_decisions")
                    self.assertEqual(json.loads(locked.read_text()), draft)
                    invalid = json.loads(tool.invoke({"path": "score.json", "decisions_json": json.dumps(decisions)}))
                    self.assertEqual(invalid["error"], "invalid_scoring_decisions")
                    self.assertEqual(json.loads(target.read_text()), draft)
                    decisions["dimension_reviews"] = [{"dimension_key": "rigor", "summary": "Decision", "name": "Replacement"}]
                    self.assertEqual(tool.invoke({"path": "score.json", "decisions_json": json.dumps(decisions)}), str(target))
                    return {"messages": []}
                return SimpleNamespace(invoke=invoke)

            with patch.object(graph, "context", return_value={"language": "zh-CN"}), patch.object(graph, "model", return_value=object()), patch.object(graph, "create_agent", side_effect=agent_factory):
                graph.stage_node("persist_literature_score")({"working_dir": str(work), "db_path": "unused", "runtime": {"error": {"code": "test-stop"}}}, {})
            result = json.loads(target.read_text())
            self.assertEqual(result["form_id"], "locked")
            self.assertEqual(result["dimension_reviews"][0], {"dimension_key": "rigor", "name": "Locked name", "summary": "Decision"})
            self.assertEqual(result["criterion_reviews"][0], {"criterion_key": "evidence", "max_score": 5, "score": 3})

    def test_render_failure_only_returns_to_a_source_prescribed_missing_stage(self):
        for missing, expected in [(["digest_slots", "reference_items"], "persist_digest"), ([], "failed")]:
            with self.subTest(missing=missing), patch.object(graph, "runtime", side_effect=[
                {"error": {"code": "citation_report_failed", "message": "render failed"}},
                {"missing_prerequisites": missing},
            ]) as source_runtime:
                value = graph.finalize({"working_dir": ".", "db_path": "runtime.db"})
                self.assertEqual(value["action"], expected)
                self.assertEqual([c.args[1] for c in source_runtime.call_args_list], ["finalize_outputs", "status"])

    def test_language_reaches_stage_and_read_only_batch_from_db(self):
        for language in ["zh-CN", "en"]:
            with self.subTest(language=language), tempfile.TemporaryDirectory() as directory:
                work = Path(directory)
                db = work / "runtime.db"
                with closing(sqlite3.connect(db)) as connection, connection:
                    connection.execute("CREATE TABLE runtime_inputs(key TEXT PRIMARY KEY, value TEXT)")
                    connection.execute("INSERT INTO runtime_inputs VALUES ('language', ?)", (language,))
                batch = work / "batch.json"
                batch.write_text(json.dumps({"citation_work_packages": []}))
                observed = {}

                def agent_factory(*, model, tools, system_prompt):
                    names = {t.name: t for t in tools}

                    def invoke(payload, config):
                        request = json.loads(payload["messages"][0]["content"])
                        if "read_batch" in names:
                            observed["batch_language"] = request["language"]
                            observed["batch_tools"] = set(names)
                            self.assertEqual(json.loads(names["read_batch"].invoke({})), {"citation_work_packages": []})
                            return {"messages": [SimpleNamespace(content='{"citation_semantic_reviews": []}')]}
                        observed["stage_language"] = request["runtime_inputs"]["language"]
                        self.assertTrue(json.loads(names["read_context"].invoke({"kind": "source"})).get("error"))
                        with self.assertRaises(ValueError):
                            names["delegate_batches"].invoke({"batch_paths": [str(work / "other-batch.json")]})
                        names["delegate_batches"].invoke({"batch_paths": [str(batch)]})
                        names["write_draft"].invoke({"path": "citation.json", "content": '{"citation_semantic_reviews": []}'})
                        names["run_stage"].invoke({"payload_path": "citation.json"})
                        return {"messages": []}
                    return SimpleNamespace(invoke=invoke)

                result = {"digest_path": "digest.md", "provenance": {}, "error": {}}
                state = {"working_dir": str(work), "db_path": str(db), "language": "conflicting-input",
                         "runtime": {"citation_batch_paths": [str(batch)]}}
                with patch.dict(os.environ, {"MODEL_ID": "controlled-test-model"}), patch.object(graph, "model", return_value=object()), patch.object(graph, "create_agent", side_effect=agent_factory), patch.object(graph, "runtime", return_value=result):
                    value = graph.stage_node("persist_citation_analysis")(state, {})
                self.assertEqual(value["result"], result)
                self.assertEqual(observed["stage_language"], language)
                self.assertEqual(observed["batch_language"], language)
                self.assertEqual(observed["batch_tools"], {"read_batch"})

    def test_successful_submission_can_be_corrected_through_runtime(self):
        with tempfile.TemporaryDirectory() as directory:
            work = Path(directory)
            db = work / "runtime.db"
            with closing(sqlite3.connect(db)) as connection, connection:
                connection.execute("CREATE TABLE runtime_inputs(key TEXT PRIMARY KEY, value TEXT)")
                connection.execute("INSERT INTO runtime_inputs VALUES ('language', 'zh-CN')")
            first = {"digest_path": "first.md", "provenance": {}, "error": {}}
            corrected = {"digest_path": "corrected.md", "provenance": {}, "error": {}}

            def agent_factory(*, model, tools, system_prompt):
                names = {t.name: t for t in tools}

                def invoke(payload, config):
                    for name, summary in [("first", "first decision"), ("corrected", "corrected decision")]:
                        names["write_draft"].invoke({"path": name + ".json", "content": json.dumps({"summary": summary})})
                        names["run_stage"].invoke({"payload_path": name + ".json"})
                    return {"messages": []}
                return SimpleNamespace(invoke=invoke)

            with patch.object(graph, "model", return_value=object()), patch.object(graph, "create_agent", side_effect=agent_factory), patch.object(graph, "runtime", side_effect=[first, corrected]) as source_runtime:
                value = graph.stage_node("persist_citation_analysis")({"working_dir": str(work), "db_path": str(db), "runtime": {}}, {})
            self.assertEqual(value["result"], corrected)
            self.assertEqual(source_runtime.call_count, 2)
            self.assertEqual([call.args[1] for call in source_runtime.call_args_list], ["persist_citation_analysis"] * 2)
            payloads = [json.loads(Path(call.args[2][-1]).read_text()) for call in source_runtime.call_args_list]
            self.assertEqual([p["summary"] for p in payloads], ["first decision", "corrected decision"])


if __name__ == "__main__":
    unittest.main()

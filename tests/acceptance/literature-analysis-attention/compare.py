"""Read-only contract checks for both runs; semantic conclusions remain explicit review."""
import json
from pathlib import Path
import sqlite3

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "graph-app/source/literature-analysis"
PUBLIC = {"digest_path": "digest.md", "references_path": "references.json",
          "citation_analysis_path": "citation_analysis.json", "citation_analysis_report_path": "citation_analysis.md",
          "literature_matching_metadata_path": "literature_matching_metadata.json", "literature_score_path": "literature_score.json"}


def read_group(name):
    work = ROOT / name
    db = work / ".literature_analysis_tmp/literature_analysis.db"
    checks, facts = {}, {}
    if not db.exists():
        return {"status": "not-run", "checks": checks, "facts": facts}
    with sqlite3.connect(f"file:{db}?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        state = dict(connection.execute("SELECT * FROM workflow_state").fetchone())
        inputs = {r["key"]: r["value"] for r in connection.execute("SELECT key,value FROM runtime_inputs")}
        facts.update(workflow_state=state, input_hash=inputs.get("input_hash"), model=inputs.get("model"), language=inputs.get("language"),
                     normalized_chars=connection.execute("SELECT length(content) FROM source_documents WHERE doc_key='normalized_source'").fetchone()[0])
        facts["receipts"] = [dict(r) for r in connection.execute("SELECT * FROM action_receipts")]
        facts["errors"] = [dict(r) for r in connection.execute("SELECT * FROM runtime_errors")]
    mirror = work / "literature-analysis.result.json"
    if not mirror.exists():
        return {"status": "incomplete", "checks": checks, "facts": facts}
    result = json.loads(mirror.read_text(encoding="utf-8"))
    facts["result"] = result
    schema = json.loads((SOURCE / "assets/output.schema.json").read_text())
    errors = [e.message for e in Draft202012Validator(schema).iter_errors(result)]
    checks["final_result_schema"] = {"passed": not errors, "errors": errors}
    checks["runtime_success"] = {"passed": not result.get("error")}
    checks["mirror_provenance_matches_db"] = {"passed": all(
        result["provenance"].get(key) == facts[key] for key in ["input_hash", "model"])}
    response_path = work / "observed-final-response.txt"
    response = response_path.read_text(encoding="utf-8") if response_path.is_file() else ""
    try:
        observed = json.loads(response)
    except ValueError:
        observed = None
    checks["final_response_is_json"] = {"passed": isinstance(observed, dict)}
    checks["final_response_matches_mirror"] = {"passed": observed == result}
    if observed is None and response.startswith("```json\n") and response.rstrip().endswith("```"):
        # Diagnose a fenced response without accepting it as the public JSON contract.
        unfenced = json.loads(response.strip()[8:-3])
        facts["fenced_response_provenance"] = unfenced.get("provenance")
    for field, filename in PUBLIC.items():
        path = Path(result.get(field, ""))
        checks[field] = {"passed": bool(result.get(field)) and path.is_absolute()
                        and path.name == filename and path.is_file() and path.parent == (work / "artifacts").resolve()}
    if (work / "artifacts/citation_analysis.json").exists():
        citation = json.loads((work / "artifacts/citation_analysis.json").read_text())
        report = work / "artifacts/citation_analysis.md"
        checks["citation_markdown_matches_json"] = {"passed": report.is_file() and report.read_text() == citation["report_md"]}
        facts["citation_items"] = len(citation.get("items", []))
        facts["citation_scope"] = citation["meta"]["scope"]
        checks["citation_language_metadata"] = {"passed": citation["meta"]["language"] == inputs["language"]}
    if (work / "artifacts/references.json").exists():
        references = json.loads((work / "artifacts/references.json").read_text())
        facts["reference_items"] = len(references if isinstance(references, list) else references.get("items", []))
        facts["reference_root_type"] = type(references).__name__
    for filename, schema_name, context_key in [("references.json", "references.schema.json", "items"),
                                               ("citation_analysis.json", "citation_analysis.schema.json", "citation_analysis")]:
        path = work / "artifacts" / filename
        schema_path = SOURCE / "assets/render_schemas" / schema_name
        if path.is_file() and schema_path.is_file():
            # These schemas validate template contexts; the templates emit the inner value.
            context = {context_key: json.loads(path.read_text())}
            errors = [e.message for e in Draft202012Validator(json.loads(schema_path.read_text())).iter_errors(context)]
            checks[filename + "_render_context_schema"] = {"passed": not errors, "errors": errors}
    score = json.loads((work / "artifacts/literature_score.json").read_text())
    facts["paper_score"] = {key: score[key] for key in ["overall_score", "confidence", "confidence_adjusted_score"]}
    checks["matching_metadata_schema"] = {"passed": json.loads((work / "artifacts/literature_matching_metadata.json").read_text()).get("schema") == "literature_matching_metadata.v1"}
    return {"status": "contract-checks-passed" if all(v["passed"] for v in checks.values()) else "contract-checks-failed",
            "checks": checks, "facts": facts, "semantic_review": "separate human review required"}


def main():
    result = {name: read_group(name) for name in ["control", "graph-run"]}
    hashes = [group["facts"].get("input_hash") for group in result.values()]
    result["same_input_hash"] = bool(hashes[0]) and hashes[0] == hashes[1]
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["same_input_hash"] and all(result[name]["status"] == "contract-checks-passed"
                                                for name in ["control", "graph-run"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())

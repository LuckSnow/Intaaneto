import json
import pytest
from scripts.pdf_research_reporting import (
    build_tables,
    read_scores,
    validate_report,
    render,
)


def synthetic_report(repeats=1):
    rows = []
    for run in range(1, repeats + 1):
        for i in range(24):
            answerable = i % 6 != 5
            qid = f"Q{i:02d}"
            rows.append(
                dict(
                    id=qid if repeats == 1 else f"{qid}-R{run}",
                    question_id=qid,
                    run=run,
                    source_id=f"PDF{i%4}",
                    question=f"Question {i}",
                    reference_answer="Reference",
                    answer="=unsafe",
                    answerable=answerable,
                    grounded=answerable,
                    error=None,
                    latency_ms=1000 + i * 100,
                    citation_scope_ok=True,
                    expected_page_hit=True if answerable else None,
                    retrieval_ms=100,
                    generation_ms=500 if answerable else None,
                    citations=[],
                )
            )
    return {
        "dataset_id": "SYNTHETIC-SOFTWARE-TEST",
        "started_at": "test",
        "finished_at": "test",
        "repeat_count": repeats,
        "question_count": 24,
        "configuration": {},
        "sources": [{"id": f"PDF{i}", "title": f"Synthetic PDF {i}"} for i in range(4)],
        "cases": rows,
    }


def test_errors_remain_in_accuracy_but_not_success_latency():
    report = synthetic_report()
    report["cases"][0].update(error="ProviderError", latency_ms=100000)
    scores = {r["id"]: 2 for r in report["cases"]}
    scores["Q00"] = 0
    stats, tables = build_tables(report, scores)
    assert stats["strict_accuracy"] == 23 / 24
    assert stats["errors"] == 1
    assert stats["max_s"] == 3.3
    assert tables["errors"] == [{"error_type": "ProviderError", "count": 1}]


def test_unrated_is_missing_not_zero():
    stats, _ = build_tables(synthetic_report(), {})
    assert stats["strict_accuracy"] is None
    assert stats["normalized_score"] is None


def test_six_pdf_thirty_question_contract():
    import copy
    report = synthetic_report()
    report['sources'] += [{'id': 'PDF4', 'title': 'NodeJS'}, {'id': 'PDF5', 'title': 'Router'}]
    report['cases'] += copy.deepcopy(report['cases'][:6])
    report['question_count'] = 30
    for i, row in enumerate(report['cases']):
        row.update(id=f'Q{i:02d}', question_id=f'Q{i:02d}', question=f'Question {i}', source_id=f'PDF{i%6}')
    rows = validate_report(report)
    stats, tables = build_tables(report, {})
    assert len(rows) == 30 and len(tables['by_pdf']) == 6
    assert stats['strict_accuracy'] is None


def test_repetitions_require_all_questions_and_runs():
    report = synthetic_report(3)
    assert len(validate_report(report)) == 72
    report["cases"][-1]["run"] = 1
    with pytest.raises(ValueError):
        validate_report(report)


def test_unfinished_run_rejected():
    report = synthetic_report()
    report.pop("finished_at")
    with pytest.raises(ValueError):
        validate_report(report)


def test_scores_cannot_hide_provider_errors(tmp_path):
    report = synthetic_report()
    report["cases"][0]["error"] = "ProviderError"
    path = tmp_path / "ratings.csv"
    path.write_text("id,score,reason\nQ00,2,wrong\n")
    with pytest.raises(ValueError):
        read_scores(path, report["cases"])


def test_matplotlib_outputs_and_private_csv(tmp_path):
    pytest.importorskip("matplotlib")
    report = synthetic_report(2)
    source = tmp_path / "input.json"
    source.write_text(json.dumps(report))
    out = tmp_path / "report"
    scores = {r["id"]: 2 for r in report["cases"]}
    render(report, scores, out, source)
    assert (out / "RESEARCH_REPORT.pdf").read_bytes().startswith(b"%PDF")
    assert (out / "score_heatmap.png").exists()
    assert (out / "tables/by_run.tex").exists()
    assert "'=unsafe" in (out / "results.csv").read_text()
    assert (out / "results.csv").stat().st_mode & 0o777 == 0o600
    provenance = json.loads((out / "provenance.json").read_text())
    assert provenance["synthetic"] and provenance["matplotlib"]

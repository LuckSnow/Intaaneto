"""Research tables and Matplotlib artifacts; pure statistics are network-free."""

from collections import Counter, defaultdict
import base64
import csv
import hashlib
import html
import json
import math
from pathlib import Path
import statistics
import sys


def percentile(values, fraction):
    values = sorted(values)
    if not values:
        return None
    position = (len(values) - 1) * fraction
    lo, hi = math.floor(position), math.ceil(position)
    return values[lo] + (values[hi] - values[lo]) * (position - lo)


def latency_stats(rows):
    values = [r["latency_ms"] / 1000 for r in rows if r["error"] is None]
    return {
        "requests": len(rows),
        "success": len(values),
        "errors": len(rows) - len(values),
        "mean_s": statistics.mean(values) if values else None,
        "median_s": statistics.median(values) if values else None,
        "p95_s": percentile(values, 0.95),
        "min_s": min(values) if values else None,
        "max_s": max(values) if values else None,
        "sd_s": statistics.stdev(values) if len(values) >= 2 else None,
    }


def summarize(rows, scores):
    complete = all(r["id"] in scores for r in rows)
    answerable = [r for r in rows if r["answerable"]]
    unsupported = [r for r in rows if not r["answerable"]]
    good = [r for r in rows if r["error"] is None]
    return dict(
        latency_stats(rows),
        reviewed=sum(r["id"] in scores for r in rows),
        strict_accuracy=(
            sum(scores[r["id"]] == 2 for r in rows) / len(rows) if complete else None
        ),
        normalized_score=(
            sum(scores[r["id"]] for r in rows) / (2 * len(rows)) if complete else None
        ),
        citation_scope_rate=sum(bool(r["citation_scope_ok"]) for r in rows) / len(rows),
        expected_page_overlap_proxy=(
            sum(bool(r["expected_page_hit"]) for r in answerable) / len(answerable)
            if answerable
            else None
        ),
        fallback_on_unsupported_proxy=(
            sum(r["error"] is None and not r["grounded"] for r in unsupported)
            / len(unsupported)
            if unsupported
            else None
        ),
        mean_retrieval_s=(
            statistics.mean(
                r["retrieval_ms"] / 1000
                for r in good
                if r.get("retrieval_ms") is not None
            )
            if any(r.get("retrieval_ms") is not None for r in good)
            else None
        ),
        mean_generation_s=(
            statistics.mean(
                r["generation_ms"] / 1000
                for r in good
                if r.get("generation_ms") is not None
            )
            if any(r.get("generation_ms") is not None for r in good)
            else None
        ),
    )


def validate_report(report):
    rows = report["cases"]
    repeat_count = report.get("repeat_count", 1)
    count = report.get("question_count", len(rows))
    if (
        not report.get("finished_at")
        or not 1 <= repeat_count <= 5
        or not 20 <= count <= 30
        or len(rows) != count * repeat_count
        or not 3 <= len(report["sources"]) <= 6
    ):
        raise ValueError(
            "Run is incomplete or outside the 20–30 questions / 3–6 PDF contract"
        )
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        raise ValueError("Duplicate result IDs")
    known_sources = {s["id"] for s in report["sources"]}
    grouped = defaultdict(list)
    for row in rows:
        if row["source_id"] not in known_sources or not isinstance(
            row["answerable"], bool
        ):
            raise ValueError("Invalid source or answerability")
        if (
            not isinstance(row["latency_ms"], (int, float))
            or not math.isfinite(row["latency_ms"])
            or row["latency_ms"] < 0
        ):
            raise ValueError("Invalid latency")
        grouped[row.get("question_id", row["id"])].append(row)
    if len(grouped) != count:
        raise ValueError("Question count differs from run metadata")
    for subset in grouped.values():
        if {r.get("run", 1) for r in subset} != set(range(1, repeat_count + 1)) or len(
            subset
        ) != repeat_count:
            raise ValueError("Missing/duplicate question repetitions")
        if (
            len(
                {
                    (
                        r["question"],
                        r["reference_answer"],
                        r["source_id"],
                        r["answerable"],
                    )
                    for r in subset
                }
            )
            != 1
        ):
            raise ValueError("Question changed between repetitions")
    return rows


def read_scores(path, rows):
    if path is None:
        return {}
    ids = {r["id"] for r in rows}
    seen, scores = set(), {}
    with Path(path).open(encoding="utf-8-sig", newline="") as stream:
        for row in csv.DictReader(stream):
            if row["id"] not in ids or row["id"] in seen:
                raise ValueError("Unknown or duplicate review ID")
            seen.add(row["id"])
            if row["score"].strip():
                if (
                    row["score"].strip() not in ("0", "1", "2")
                    or not row.get("reason", "").strip()
                ):
                    raise ValueError("Completed scores need 0/1/2 and a reason")
                scores[row["id"]] = int(row["score"])
    if any(r["error"] is not None and scores.get(r["id"], 0) != 0 for r in rows):
        raise ValueError("System/provider errors must receive score 0")
    return scores


def safe_cell(value):
    value = str(value if value is not None else "")
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) else value


def write_csv(path, fields, rows):
    with Path(path).open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: safe_cell(row.get(key)) for key in fields})
    Path(path).chmod(0o600)


def build_tables(report, scores):
    rows = validate_report(report)
    overall = summarize(rows, scores)
    overall.update(
        question_count=report.get("question_count", len(rows)),
        repeat_count=report.get("repeat_count", 1),
    )
    tables = {
        "overall": [{"metric": k, "value": v} for k, v in overall.items()],
        "by_pdf": [],
        "by_run": [],
        "by_answerability": [],
        "by_question": [],
        "index_sources": report["sources"],
        "errors": [],
        "citations": [],
    }
    for source in report["sources"]:
        tables["by_pdf"].append(
            dict(
                source_id=source["id"],
                title=source["title"],
                **summarize(
                    [r for r in rows if r["source_id"] == source["id"]], scores
                ),
            )
        )
    for run in range(1, overall["repeat_count"] + 1):
        tables["by_run"].append(
            dict(
                run=run,
                **summarize([r for r in rows if r.get("run", 1) == run], scores),
            )
        )
    for flag in (True, False):
        subset = [r for r in rows if r["answerable"] == flag]
        if subset:
            tables["by_answerability"].append(
                dict(answerable=flag, **summarize(subset, scores))
            )
    questions = defaultdict(list)
    for row in rows:
        questions[row.get("question_id", row["id"])].append(row)
        for citation in row.get("citations", []):
            tables["citations"].append(
                {
                    "case_id": row["id"],
                    "chunk_id": citation.get("chunk_id"),
                    "lesson_id": citation.get("lesson_id"),
                    "source_id": citation.get("source_id"),
                    "score": citation.get("score"),
                    "page_start": citation.get("location", {}).get("page_start"),
                    "page_end": citation.get("location", {}).get("page_end"),
                }
            )
    for question, subset in questions.items():
        tables["by_question"].append(
            dict(
                question_id=question,
                source_id=subset[0]["source_id"],
                grounded_consistency=max(
                    Counter((r["error"], r["grounded"]) for r in subset).values()
                )
                / len(subset),
                **summarize(subset, scores),
            )
        )
    tables["errors"] = [
        {"error_type": key, "count": count}
        for key, count in Counter(r["error"] for r in rows if r["error"]).items()
    ]
    tables["scores"] = [
        {"score": score, "count": sum(v == score for v in scores.values())}
        for score in (0, 1, 2)
    ]
    tables["scores"].append({"score": "pending", "count": len(rows) - len(scores)})
    tables["outcomes"] = []
    for source in report["sources"]:
        subset = [r for r in rows if r["source_id"] == source["id"]]
        tables["outcomes"].append(
            {
                "source_id": source["id"],
                "grounded": sum(r["error"] is None and r["grounded"] for r in subset),
                "fallback": sum(
                    r["error"] is None and not r["grounded"] for r in subset
                ),
                "error": sum(r["error"] is not None for r in subset),
            }
        )
    return overall, tables


def display(value):
    return (
        "— / chưa có dữ liệu"
        if value is None
        else f"{value:.4f}" if isinstance(value, float) else str(value)
    )


def latex_cell(value):
    mapping = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    return "".join(mapping.get(c, c) for c in display(value))


def export_tables(out, tables):
    folder = out / "tables"
    folder.mkdir(exist_ok=True, mode=0o700)
    for name, rows in tables.items():
        fields = list(dict.fromkeys(key for row in rows for key in row)) or ["status"]
        write_csv(folder / f"{name}.csv", fields, rows)
        # Compact numeric summaries for manuscripts; raw answers remain in CSV.
        numeric = [
            key
            for key in fields
            if key not in ("title", "pdf_sha256", "source_checksum", "storage_name")
        ]
        if len(numeric) > 8:
            numeric = [
                key
                for key in (
                    "source_id",
                    "run",
                    "question_id",
                    "requests",
                    "errors",
                    "mean_s",
                    "p95_s",
                    "strict_accuracy",
                )
                if key in fields
            ]
        tex = [
            r"\begin{tabular}{" + "l" * len(numeric) + "}",
            r"\hline",
            " & ".join(latex_cell(key) for key in numeric) + r" \\",
            r"\hline",
        ]
        tex += [
            " & ".join(latex_cell(row.get(key)) for key in numeric) + r" \\"
            for row in rows
        ]
        tex += [r"\hline", r"\end{tabular}"]
        (folder / f"{name}.tex").write_text("\n".join(tex), encoding="utf-8")


def plot_research(report, scores, tables, out, review_method="human"):
    import matplotlib

    # Agg works without a desktop/X server.
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_pdf import PdfPages
    import numpy as np

    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "pdf.fonttype": 42,
            "svg.fonttype": "path",
            "axes.spines.top": False,
            "axes.spines.right": False,
        }
    )
    rows = report["cases"]
    figures = []
    synthetic = "SYNTHETIC" in report["dataset_id"].upper()

    def save(name, fig):
        if synthetic:
            fig.suptitle(
                "DỮ LIỆU GIẢ LẬP — KIỂM TRA PHẦN MỀM", color="#a33300", fontsize=10
            )
        elif review_method == "ai_assisted_preliminary" and name in (
            "accuracy_by_pdf", "score_distribution", "score_heatmap"
        ):
            fig.suptitle("CHẤM SƠ BỘ BỞI CODEX — CHƯA CÓ NGƯỜI CHẤM ĐỘC LẬP", fontsize=9)
        for ext in ("png", "svg", "pdf"):
            fig.savefig(out / f"{name}.{ext}", dpi=300, facecolor="white")
        figures.append((name, fig))

    def empty(ax, message="Chưa có yêu cầu thành công"):
        ax.text(0.5, 0.5, message, ha="center", va="center", transform=ax.transAxes)
        ax.set_xticks([])
        ax.set_yticks([])

    fig, ax = plt.subplots(figsize=(11, 5), layout="constrained")
    questions = tables["by_question"]
    ax.bar(
        range(len(questions)),
        [r["mean_s"] if r["mean_s"] is not None else np.nan for r in questions],
        color="#0072B2",
    )
    ax.set_xticks(
        range(len(questions)),
        [r["question_id"] for r in questions],
        rotation=65,
        ha="right",
    )
    ax.set(
        ylabel="Giây",
        title="Thời gian trung bình mỗi câu — chỉ yêu cầu thành công",
        ylim=(0, None),
    )
    for i, row in enumerate(questions):
        if row["mean_s"] is None:
            ax.text(i, 0, "Không có", rotation=90, va="bottom", fontsize=7)
    save("latency_by_question", fig)
    fig, ax = plt.subplots(figsize=(8, 5), layout="constrained")
    for i, source in enumerate(report["sources"], 1):
        values = [
            r["latency_ms"] / 1000
            for r in rows
            if r["source_id"] == source["id"] and r["error"] is None
        ]
        if values:
            ax.boxplot([values], positions=[i], widths=0.45, showfliers=True)
            ax.scatter([i] * len(values), values, marker="x", color="#0072B2", s=16)
        else:
            ax.text(i, 0, "Không có", rotation=90, va="bottom")
    ax.set_xticks(
        range(1, len(report["sources"]) + 1), [s["id"] for s in report["sources"]]
    )
    ax.set(
        ylabel="Giây",
        title="Phân bố latency theo PDF — thành công; dấu × là từng yêu cầu",
        ylim=(0, None),
    )
    save("latency_by_pdf", fig)
    values = [r["latency_ms"] / 1000 for r in rows if r["error"] is None]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4), layout="constrained")
    if values:
        counts, edges = np.histogram(values, bins="sturges")
        axes[0].hist(values, bins=edges, color="#0072B2", edgecolor="white")
        axes[1].step(
            sorted(values),
            np.arange(1, len(values) + 1) / len(values),
            where="post",
            color="#0072B2",
        )
        write_csv(
            out / "tables/histogram_bins.csv",
            ["lower_s", "upper_s", "count"],
            [
                dict(lower_s=float(edges[i]), upper_s=float(edges[i + 1]), count=int(n))
                for i, n in enumerate(counts)
            ],
        )
    else:
        for ax in axes:
            empty(ax)
    axes[0].set(
        xlabel="Giây", ylabel="Số yêu cầu", title="Histogram — bins theo Sturges"
    )
    axes[1].set(
        xlabel="Giây",
        ylabel="Tỷ lệ tích lũy",
        title="ECDF latency thành công",
        ylim=(0, 1),
    )
    save("latency_distribution", fig)
    fig, ax = plt.subplots(figsize=(8, 4), layout="constrained")
    outcomes = tables["outcomes"]
    bottom = np.zeros(len(outcomes))
    for key, label, color, hatch in [
        ("grounded", "Grounded (proxy)", "#0072B2", ""),
        ("fallback", "Fallback", "#E69F00", "//"),
        ("error", "Lỗi", "#555555", "xx"),
    ]:
        heights = [r[key] for r in outcomes]
        ax.bar(
            [r["source_id"] for r in outcomes],
            heights,
            bottom=bottom,
            label=label,
            color=color,
            hatch=hatch,
        )
        bottom += heights
    ax.set(ylabel="Số yêu cầu", title="Kết quả kỹ thuật theo PDF")
    ax.legend()
    save("outcomes_by_pdf", fig)
    fig, ax = plt.subplots(figsize=(8, 4), layout="constrained")
    if len(scores) == len(rows):
        ax.bar(
            [r["source_id"] for r in tables["by_pdf"]],
            [r["strict_accuracy"] * 100 for r in tables["by_pdf"]],
            color="#0072B2",
        )
        ax.set(
            ylabel="Đạt đủ 2/2 (%)",
            title="Accuracy mô tả theo PDF — không có suy luận tổng quát",
            ylim=(0, 100),
        )
    else:
        empty(
            ax,
            f"Chưa chấm đủ: {len(scores)}/{len(rows)} yêu cầu\nKhông tính accuracy từ grounded/citation",
        )
    save("accuracy_by_pdf", fig)
    fig, ax = plt.subplots(figsize=(8, 4), layout="constrained")
    ax.bar(
        ["0 — sai/lỗi", "1 — một phần", "2 — đầy đủ", "Chưa chấm"],
        [r["count"] for r in tables["scores"]],
        color=["#555555", "#E69F00", "#0072B2", "#cccccc"],
    )
    ax.set(ylabel="Số yêu cầu", title="Phân bố điểm do người chấm cung cấp")
    save("score_distribution", fig)
    fig, ax = plt.subplots(
        figsize=(8, max(5, len(questions) * 0.24)), layout="constrained"
    )
    qids = [q["question_id"] for q in questions]
    runs = report.get("repeat_count", 1)
    matrix = np.full((len(qids), runs), np.nan)
    for r in rows:
        if r["id"] in scores:
            matrix[qids.index(r.get("question_id", r["id"])), r.get("run", 1) - 1] = (
                scores[r["id"]]
            )
    cmap = plt.get_cmap("cividis", 3).copy()
    cmap.set_bad("#dddddd")
    im = ax.imshow(
        np.ma.masked_invalid(matrix),
        vmin=0,
        vmax=2,
        cmap=cmap,
        aspect="auto",
        interpolation="nearest",
    )
    for y in range(len(qids)):
        for x in range(runs):
            ax.text(
                x,
                y,
                "—" if np.isnan(matrix[y, x]) else str(int(matrix[y, x])),
                ha="center",
                va="center",
                color="black",
                bbox={
                    "facecolor": "white",
                    "alpha": 0.8,
                    "edgecolor": "none",
                    "pad": 1,
                },
            )
    ax.set_yticks(range(len(qids)), qids)
    ax.set_xticks(range(runs), [f"Lần {i+1}" for i in range(runs)])
    ax.set_title("Điểm từng câu qua các lần chạy — dấu “—” là chưa chấm")
    fig.colorbar(im, ax=ax, ticks=[0, 1, 2], label="Điểm rubric")
    save("score_heatmap", fig)
    with PdfPages(out / "RESEARCH_REPORT.pdf") as pdf:
        import textwrap
        fig, ax = plt.subplots(figsize=(11.7, 8.3), layout="constrained")
        ax.axis("off")
        subtitle = ("Chấm nội dung sơ bộ có AI hỗ trợ bởi Codex; chưa được giảng viên duyệt."
                    if review_method == "ai_assisted_preliminary" else "Điểm nội dung từ phiếu chấm cung cấp; nếu chưa có điểm thì accuracy để trống.")
        cover = ["BÁO CÁO THỰC NGHIỆM RAG TRÊN PDF", report['dataset_id'],
                 f"{len(report['sources'])} PDF; {report.get('question_count', len(rows))} câu; {report.get('repeat_count', 1)} lần/câu; {len(rows)} yêu cầu.",
                 f"UTC: {report['started_at']} → {report['finished_at']}", subtitle,
                 "Đo dịch vụ RAG backend bằng actor được cấp quyền; embedding warm; không gồm browser/HTTP hoặc ingestion.",
                 "Accuracy = số phản hồi đạt 2/2 / toàn bộ yêu cầu. Lỗi provider phải chấm 0. Grounded, citation scope, page overlap là proxy, không phải accuracy ngữ nghĩa.",
                 "Các lần chạy của cùng câu phụ thuộc nhau. Đây là thống kê mô tả trên mẫu nhỏ, chưa có holdout hoặc hai người chấm độc lập.",
                 "Latency summaries chỉ dùng yêu cầu thành công; SD là độ phân tán, P95 nội suy tuyến tính. Khoảng nghỉ giữa các lượt không tính vào latency.",
                 "Dataset, phản hồi gốc, phiếu chấm, checksum/cấu hình và quy tắc biến đổi được lưu cùng báo cáo trong JSON/CSV/provenance.json."]
        ax.text(.05, .95, '\n\n'.join(textwrap.fill(line, 105) for line in cover), va='top', fontsize=12)
        pdf.savefig(fig)
        plt.close(fig)
        # Numeric tables plus plots in one shareable document.
        for name in ("overall", "by_pdf", "by_run", "by_answerability", "by_question"):
            table_rows = tables[name]
            fields = list(table_rows[0]) if table_rows else []
            if len(fields) > 8:
                fields = [
                    f
                    for f in (
                        "source_id",
                        "run",
                        "question_id",
                        "requests",
                        "errors",
                        "mean_s",
                        "p95_s",
                        "strict_accuracy",
                    )
                    if f in fields
                ]
            fig, ax = plt.subplots(figsize=(11.7, 8.3), layout="constrained")
            ax.axis("off")
            ax.set_title(f'{name} — {report["dataset_id"]}', pad=20)
            if review_method == "ai_assisted_preliminary":
                fig.suptitle("CHẤM SƠ BỘ BỞI CODEX — CHƯA CÓ NGƯỜI CHẤM ĐỘC LẬP", fontsize=10)
            cell_text = [[display(r.get(f)) for f in fields] for r in table_rows]
            table = ax.table(
                cellText=cell_text, colLabels=fields, loc="center", cellLoc="left"
            )
            table.auto_set_font_size(False)
            table.set_fontsize(8)
            table.scale(1, 1.4)
            pdf.savefig(fig)
            plt.close(fig)
        for _, fig in figures:
            pdf.savefig(fig)
            plt.close(fig)
    return [name for name, _ in figures]


def render(report, scores, out, results_path, review_method="human"):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True, mode=0o700)
    if out.is_symlink() or any(p.is_symlink() for p in out.rglob("*")):
        raise ValueError("Output directory cannot contain symlinks")
    overall, tables = build_tables(report, scores)
    rows = report["cases"]
    export_tables(out, tables)
    if not (out / "ratings.csv").exists():
        write_csv(
            out / "ratings.csv",
            ["id", "score", "reason"],
            [{"id": r["id"]} for r in rows],
        )
    fields = [
        "id",
        "question_id",
        "run",
        "source_id",
        "question",
        "reference_answer",
        "answer",
        "answerable",
        "grounded",
        "error",
        "latency_ms",
        "retrieval_ms",
        "generation_ms",
        "citation_scope_ok",
        "expected_page_hit",
        "score",
    ]
    write_csv(
        out / "results.csv", fields, [dict(r, score=scores.get(r["id"])) for r in rows]
    )
    (out / "metrics.json").write_text(
        json.dumps(overall, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    figures = plot_research(report, scores, tables, out, review_method=review_method)
    import matplotlib

    provenance = {
        "dataset_id": report["dataset_id"],
        "dataset_sha256": report.get("dataset_sha256"),
        "results_sha256": hashlib.sha256(Path(results_path).read_bytes()).hexdigest(),
        "python": sys.version.split()[0],
        "matplotlib": matplotlib.__version__,
        "configuration": report["configuration"],
        "started_at": report["started_at"],
        "finished_at": report["finished_at"],
        "ratings_completed": len(scores),
        "review_method": review_method if scores else "unreviewed",
        "scores": scores,
        "methods": {
            "latency": "warm RAG service; successful requests only in descriptive latency summaries",
            "p95": "linear interpolation",
            "sd": "sample SD; undefined with fewer than two successes",
            "accuracy": "score 2 count / all requests; repeated responses are dependent, no row-wise CI",
            "histogram": "Sturges; explicit edges in tables/histogram_bins.csv",
            "missing": "null/blank, never zero; failed request timings remain in results.csv",
        },
        "figures": figures,
        "formats": ["png 300dpi", "svg", "pdf"],
        "synthetic": "SYNTHETIC" in report["dataset_id"].upper(),
    }
    (out / "provenance.json").write_text(
        json.dumps(provenance, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    notes = [
        ("Điểm nội dung được Codex chấm sơ bộ có AI hỗ trợ theo đáp án/rubric. Đây không phải kết quả chấm độc lập của giảng viên; cần duyệt trước khi dùng làm kết luận accuracy trong báo cáo."
         if review_method == "ai_assisted_preliminary" else "Điểm nội dung lấy từ phiếu chấm cung cấp; không có điểm tự suy ra từ cờ grounded."),
        "Phạm vi: dịch vụ RAG backend với actor được cấp quyền, embedding đã khởi động; không gồm HTTP/browser, đăng nhập, lưu chat hoặc ingestion.",
        f'{overall["question_count"]} câu hỏi, {overall["repeat_count"]} lần chạy/câu, {len(rows)} yêu cầu. Các lần chạy của cùng câu không độc lập.',
        "Accuracy chỉ tính khi đủ điểm người chấm; lỗi hệ thống phải chấm 0. Grounded, citation scope và chồng lấp trang chỉ là proxy kỹ thuật.",
        "Đáp án tham chiếu cần giảng viên duyệt. Chưa có holdout, mẫu ngẫu nhiên hoặc bằng chứng đồng thuận hai người chấm. Không suy luận hiệu quả tổng quát từ mẫu nhỏ.",
        "TB/median/P95/SD chỉ dùng yêu cầu thành công; số lỗi vẫn được giữ và báo cáo. SD là độ phân tán, không phải khoảng tin cậy.",
        "Biểu đồ boxplot: hộp Q1–Q3, đường median, râu 1.5 IQR; dấu × là từng phản hồi. Không có dữ liệu khác với latency bằng 0.",
        "Nguồn dữ liệu, cấu hình, checksum, phiên bản phần mềm và quy tắc biến đổi ghi trong provenance.json; bảng LaTeX dùng UTF-8 (XeLaTeX/LuaLaTeX).",
    ]
    title = "# Báo cáo nghiên cứu RAG trên PDF"
    if provenance["synthetic"]:
        title += " — DỮ LIỆU GIẢ LẬP, KHÔNG PHẢI THỰC NGHIỆM"
    lines = [
        title,
        "",
        f'Dataset: `{report["dataset_id"]}`. UTC: {report["started_at"]} → {report["finished_at"]}.',
        "",
    ]
    body = [
        f'<h1>{html.escape(title.lstrip("# "))}</h1>',
        "<p>" + html.escape(lines[2]) + "</p>",
    ]
    for note in notes:
        lines += [note, ""]
        body.append("<p>" + html.escape(note) + "</p>")
    for name, table_rows in tables.items():
        fields = list(dict.fromkeys(k for row in table_rows for k in row))
        lines += [f"## {name}", ""]
        body.append("<h2>" + html.escape(name) + "</h2>")
        if not table_rows:
            lines += ["Không có bản ghi.", ""]
            body.append("<p>Không có bản ghi.</p>")
            continue
        lines += [
            "| " + " | ".join(fields) + " |",
            "|" + "|".join("---" for _ in fields) + "|",
        ]
        body.append(
            '<div class="scroll"><table><tr>'
            + "".join("<th>" + html.escape(f) + "</th>" for f in fields)
            + "</tr>"
        )
        for row in table_rows:
            lines.append(
                "| "
                + " | ".join(
                    display(row.get(f)).replace("|", r"\|").replace("\n", " ")
                    for f in fields
                )
                + " |"
            )
            body.append(
                "<tr>"
                + "".join(
                    "<td>" + html.escape(display(row.get(f))) + "</td>" for f in fields
                )
                + "</tr>"
            )
        body.append("</table></div>")
        lines.append("")
    for name in figures:
        lines += [f"![{name}]({name}.png)", ""]
        body.append(
            f'<figure><img alt="{name}; dữ liệu gốc trong bảng tương ứng" src="data:image/png;base64,'
            + base64.b64encode((out / f"{name}.png").read_bytes()).decode()
            + '"><figcaption>'
            + html.escape(name)
            + "</figcaption></figure>"
        )
    lines += [
        "## Cấu hình",
        "",
        "```json",
        json.dumps(report["configuration"], ensure_ascii=False, indent=2),
        "```",
    ]
    body.append(
        "<h2>Cấu hình</h2><pre>"
        + html.escape(json.dumps(report["configuration"], ensure_ascii=False, indent=2))
        + "</pre>"
    )
    body.append("<h2>Đối chiếu từng câu</h2>")
    for r in rows:
        body.append(
            "<details><summary>"
            + html.escape(r["id"])
            + "</summary><p><strong>Câu hỏi:</strong> "
            + html.escape(r["question"])
            + "</p><p><strong>Chuẩn:</strong> "
            + html.escape(r["reference_answer"])
            + "</p><p><strong>Hệ thống:</strong> "
            + html.escape(r["answer"])
            + "</p></details>"
        )
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    (out / "REPORT.html").write_text(
        '<!doctype html><html lang="vi"><meta charset="utf-8"><title>Báo cáo RAG PDF</title><style>body{font:15px system-ui;max-width:1200px;margin:30px auto;padding:20px;color:#172033}table{border-collapse:collapse;font-size:12px}th,td{border:1px solid #ccd5e0;padding:7px}.scroll{overflow:auto}img{max-width:100%}p{line-height:1.6}details{margin:12px 0}pre{white-space:pre-wrap}</style>'
        + "".join(body)
        + "</html>",
        encoding="utf-8",
    )
    for path in out.rglob("*"):
        if path.is_file():
            path.chmod(0o600)
    return overall

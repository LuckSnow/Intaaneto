"""Export private research tables and Matplotlib PNG/SVG/PDF figures."""

import argparse
import json
from pathlib import Path

from pdf_research_reporting import read_scores, render, validate_report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--ratings", type=Path)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--review-method", choices=['human', 'ai_assisted_preliminary'], default='human')
    args = parser.parse_args()
    try:
        report = json.loads(args.results.read_text(encoding="utf-8"))
        rows = validate_report(report)
        scores = read_scores(args.ratings, rows)
        render(report, scores, args.output_dir, args.results, review_method=args.review_method)
    except ImportError:
        parser.error(
            "Install the optional reporting dependencies: pip install -r backend/requirements-research.txt"
        )
    except (ValueError, KeyError, OSError) as exc:
        parser.error(str(exc))
    print(
        f'Report: {args.output_dir / "REPORT.html"}; ratings: {len(scores)}/{len(rows)}'
    )


if __name__ == "__main__":
    main()

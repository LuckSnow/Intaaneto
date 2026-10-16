"""Host CLI: bulk PDF import → repeated RAG evaluation → Matplotlib report.

Run at the repository root. Docker CLI must have access to local host files.
All cloud writes and provider calls happen only on an explicit manual command.
"""

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tarfile
import tempfile
import uuid

ROOT = Path(__file__).resolve().parents[2]


def private_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with os.fdopen(
        os.open(path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW, 0o600),
        "wb",
    ) as f:
        f.write(data)
    path.chmod(0o600)


class Docker:
    def __init__(self, executable):
        self.base = [executable, "compose"]

    def execute(self, argv, **kwargs):
        return subprocess.run(self.base + argv, cwd=ROOT, check=True, **kwargs)

    def put(self, local, remote):
        code = 'import os,sys; f=os.open(sys.argv[1],os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600); s=os.fdopen(f,"wb"); s.write(sys.stdin.buffer.read()); s.close()'
        self.execute(
            ["exec", "-T", "backend", "python", "-c", code, remote],
            input=Path(local).read_bytes(),
        )

    def fetch(self, remote, local):
        data = self.execute(
            ["exec", "-T", "backend", "cat", remote], capture_output=True
        ).stdout
        json.loads(data)  # Never save an error message as research JSON.
        private_write(local, data)

    def clean_files(self, paths):
        code = (
            "import os,sys; [os.unlink(p) for p in sys.argv[1:] if os.path.isfile(p)]"
        )
        self.execute(["exec", "-T", "backend", "python", "-c", code, *paths])


def upload(args, docker, manifest):
    folder = args.pdf_dir
    if folder.is_symlink() or not folder.is_dir():
        raise ValueError("Expected a real PDF directory")
    files = sorted(p for p in folder.iterdir() if p.suffix.lower() == ".pdf")
    if not 1 <= len(files) <= 50 or any(
        p.is_symlink() or not p.is_file() or p.stat().st_size > 20 * 1024 * 1024
        for p in files
    ):
        raise ValueError("Expected 1–50 regular PDFs, each at most 20 MB")
    name = "intaaneto-pdf-batch-" + uuid.uuid4().hex
    remote_dir = "/tmp/" + name
    remote_manifest = remote_dir + "-manifest.json"
    try:
        # Copy only selected PDFs, never arbitrary files in the source directory.
        # Stream across stdin so Windows Docker CLI also works from WSL.
        receiver = '''import os,sys,tarfile,shutil
from pathlib import PurePosixPath
destination=sys.argv[1]
os.mkdir(destination,0o700)
count=0
with tarfile.open(fileobj=sys.stdin.buffer,mode="r|") as archive:
 for member in archive:
  count+=1
  if count>50 or not member.isfile() or member.name!=PurePosixPath(member.name).name or not member.name.lower().endswith(".pdf") or member.size>20*1024*1024:
   raise ValueError("Invalid PDF transfer")
  fd=os.open(os.path.join(destination,member.name),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
  with os.fdopen(fd,"wb") as output:
   shutil.copyfileobj(archive.extractfile(member),output)
'''
        with tempfile.TemporaryFile() as transfer:
            with tarfile.open(fileobj=transfer, mode="w") as archive:
                for path in files:
                    archive.add(path, arcname=path.name, recursive=False)
            transfer.seek(0)
            docker.execute(["exec", "-T", "backend", "python", "-c", receiver, remote_dir], stdin=transfer)
        cmd = [
            "exec",
            "-T",
            "backend",
            "python",
            "manage.py",
            "import_pdf_batch",
            "--directory",
            remote_dir,
            "--actor-id",
            str(args.actor_id),
            "--course-id",
            str(args.course_id),
            "--output",
            remote_manifest,
        ]
        if args.execute:
            cmd.append("--execute")
        if args.wait:
            cmd += ["--wait", "--wait-seconds", str(args.wait_seconds)]
        try:
            docker.execute(cmd)
        finally:
            # Preserve partial/failed file statuses even when the command exits nonzero.
            try:
                docker.fetch(remote_manifest, manifest)
            except (subprocess.CalledProcessError, ValueError):
                pass
    finally:
        code = "import shutil,sys,os; shutil.rmtree(sys.argv[1],ignore_errors=True); p=sys.argv[2]; os.unlink(p) if os.path.isfile(p) else None"
        docker.execute(
            ["exec", "-T", "backend", "python", "-c", code, remote_dir, remote_manifest]
        )


def evaluate(args, docker, results, manifest):
    if not args.confirm_provider_cost:
        raise ValueError("--confirm-provider-cost required for live RAG evaluation")
    prefix = "/tmp/intaaneto-pdf-eval-" + uuid.uuid4().hex
    dataset_path, manifest_path, output_path = (
        prefix + "-dataset.json",
        prefix + "-manifest.json",
        prefix + "-results.json",
    )
    try:
        docker.put(args.dataset, dataset_path)
        if manifest:
            docker.put(manifest, manifest_path)
        cmd = [
            "exec",
            "-T",
            "backend",
            "python",
            "scripts/evaluate_pdf_qa.py",
            "--dataset",
            dataset_path,
            "--output",
            output_path,
            "--actor-id",
            str(args.actor_id),
            "--repeats",
            str(args.repeats),
            "--confirm-provider-cost",
            "--request-delay-seconds",
            str(args.request_delay_seconds),
        ]
        if manifest:
            cmd += ["--ingestion-manifest", manifest_path]
        try:
            docker.execute(cmd)
        finally:
            try:
                docker.fetch(output_path, results)
            except (subprocess.CalledProcessError, ValueError):
                pass
    finally:
        docker.clean_files([dataset_path, manifest_path, output_path])


def reporting(args, results, out):
    from pdf_research_reporting import read_scores, render, validate_report

    report = json.loads(Path(results).read_text())
    rows = validate_report(report)
    scores = read_scores(args.ratings, rows)
    render(report, scores, out, results, review_method=getattr(args, 'review_method', 'human'))
    print(f'Report: {out / "REPORT.html"}; {len(scores)}/{len(rows)} completed ratings')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--docker", default="docker", help="Docker CLI executable")
    sub = p.add_subparsers(dest="action", required=True)
    for action in ("upload", "run", "pipeline", "report"):
        s = sub.add_parser(action)
        s.add_argument(
            "--output-dir", type=Path, default=ROOT / "artifacts/rag_pdf_eval"
        )
        if action in ("upload", "pipeline"):
            s.add_argument("--pdf-dir", type=Path, required=True)
            s.add_argument("--course-id", type=int, required=True)
            s.add_argument("--execute", action="store_true")
            s.add_argument("--wait", action="store_true")
            s.add_argument("--wait-seconds", type=int, default=600)
        if action in ("upload", "run", "pipeline"):
            s.add_argument("--actor-id", type=int, required=True)
        if action in ("run", "pipeline"):
            s.add_argument("--dataset", type=Path, required=True)
            s.add_argument("--manifest", type=Path)
            s.add_argument("--repeats", type=int, choices=range(1, 6), default=1)
            s.add_argument("--confirm-provider-cost", action="store_true")
            s.add_argument("--request-delay-seconds", type=float, default=0)
        if action in ("run", "pipeline", "report"):
            s.add_argument("--ratings", type=Path)
            s.add_argument("--review-method", choices=['human', 'ai_assisted_preliminary'], default='human')
        if action == "report":
            s.add_argument("--results", type=Path, required=True)
    args = p.parse_args()
    try:
        if args.action == "pipeline" and (
            not args.execute or not args.confirm_provider_cost
        ):
            p.error(
                "pipeline requires --execute and --confirm-provider-cost before any side effects"
            )
        if args.action in ("run", "pipeline", "report"):
            import matplotlib  # Check optional dependency before any billable request.
        docker = Docker(args.docker)
        if args.action in ("upload", "pipeline"):
            if args.wait and not args.execute:
                p.error("--wait requires --execute")
            if args.action == "pipeline":
                args.wait = True
            manifest = args.output_dir / "import-manifest.json"
            upload(args, docker, manifest)
            print(f"Manifest: {manifest}")
        if args.action in ("run", "pipeline"):
            results = args.output_dir / "results.json"
            manifest = (
                args.output_dir / "import-manifest.json"
                if args.action == "pipeline"
                else args.manifest
            )
            evaluate(args, docker, results, manifest)
            reporting(args, results, args.output_dir / "report")
        if args.action == "report":
            reporting(args, args.results, args.output_dir / "report")
    except (ValueError, ImportError, subprocess.CalledProcessError, OSError) as exc:
        p.error(
            f"{type(exc).__name__}: operation stopped. Inspect the private manifest; install requirements-research.txt for reporting."
        )


if __name__ == "__main__":
    main()

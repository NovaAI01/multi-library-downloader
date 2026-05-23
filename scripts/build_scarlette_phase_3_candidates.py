#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import filter_scarlette_album_candidates as candidate_filter

DEFAULT_INPUT = Path("reports/scarlette_discovery/filtered_album_candidates.csv")
DEFAULT_OUTPUT_DIR = Path("reports/scarlette_track_phase_3")
DEFAULT_MANIFEST = Path.home() / "Music/ScarletteTrackLibrary/_manifests/source_manifest.csv"
DEFAULT_KNOWN_BAD_URLS = Path("config/scarlette_known_bad_urls.txt")
DEFAULT_LIMIT = 40

URLS_OUT = "track_phase_3a_clean_urls.txt"
REVIEW_OUT = "track_phase_3a_review.csv"
REJECTED_OUT = "track_phase_3a_rejected.csv"

INPUT_FIELDS = ["artist", "search_query", "url", "title"]
REVIEW_FIELDS = INPUT_FIELDS + ["review_status", "review_notes"]
REJECTED_FIELDS = INPUT_FIELDS + ["reject_reason"]


def canonical_url(value: str) -> str:
    url = value.strip()
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if host in {"www.youtube.com", "youtube.com", "m.youtube.com"}:
        video_ids = parse_qs(parsed.query).get("v", [])
        if video_ids and video_ids[0]:
            return f"https://www.youtube.com/watch?v={video_ids[0]}"

    if host == "youtu.be":
        video_id = parsed.path.strip("/")
        if video_id:
            return f"https://www.youtube.com/watch?v={video_id}"

    return url


def read_plain_url_file(path: Path) -> set[str]:
    if not path.exists():
        return set()

    urls: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            urls.add(canonical_url(value))
    return urls


def read_manifest_urls(path: Path) -> set[str]:
    if not path.exists():
        return set()

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if not reader.fieldnames or "url" not in reader.fieldnames:
            raise ValueError(f"manifest missing url column: {path}")
        return {
            canonical_url(row["url"])
            for row in reader
            if row.get("url", "").strip()
            and row.get("status", "").strip().lower() in {"", "success", "downloaded"}
        }


def read_candidate_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise FileNotFoundError(f"missing filtered candidate CSV: {path}")

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        missing = [field for field in INPUT_FIELDS if field not in fieldnames]
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(missing)}")
        return [{field: row.get(field, "") for field in INPUT_FIELDS} for row in reader]


def rejected_row(row: dict[str, str], reason: str) -> dict[str, str]:
    return {**{field: row.get(field, "") for field in INPUT_FIELDS}, "reject_reason": reason}


def review_row(row: dict[str, str]) -> dict[str, str]:
    return {
        **{field: row.get(field, "") for field in INPUT_FIELDS},
        "review_status": "needs_manual_review",
        "review_notes": "",
    }


def build_candidates(
    rows: list[dict[str, str]],
    downloaded_urls: set[str],
    known_bad_urls: set[str],
    limit: int,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    accepted: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    seen_urls: set[str] = set()

    for row in rows:
        url = canonical_url(row.get("url", ""))
        row = {**row, "url": url}

        if not url:
            rejected.append(rejected_row(row, "missing_url"))
            continue

        if url in seen_urls:
            rejected.append(rejected_row(row, "duplicate_url"))
            continue
        seen_urls.add(url)

        if url in downloaded_urls:
            rejected.append(rejected_row(row, "already_downloaded"))
            continue

        if url in known_bad_urls:
            rejected.append(rejected_row(row, "known_bad_url"))
            continue

        reason = candidate_filter.row_reason(row, known_bad_urls)
        if reason:
            rejected.append(rejected_row(row, reason))
            continue

        if len(accepted) >= limit:
            rejected.append(rejected_row(row, "over_limit"))
            continue

        accepted.append(review_row(row))

    return accepted, rejected


def write_outputs(output_dir: Path, accepted: list[dict[str, str]], rejected: list[dict[str, str]]) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / URLS_OUT).open("w", encoding="utf-8") as f:
        for row in accepted:
            f.write(row["url"] + "\n")

    with (output_dir / REVIEW_OUT).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(accepted)

    with (output_dir / REJECTED_OUT).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REJECTED_FIELDS)
        writer.writeheader()
        writer.writerows(rejected)


def run(
    input_csv: Path,
    manifest_csv: Path,
    known_bad_file: Path,
    output_dir: Path,
    limit: int,
    dry_run: bool,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    if limit < 1:
        raise ValueError("--limit must be greater than zero")

    rows = read_candidate_rows(input_csv)
    downloaded_urls = read_manifest_urls(manifest_csv)
    known_bad_urls = read_plain_url_file(known_bad_file)
    accepted, rejected = build_candidates(rows, downloaded_urls, known_bad_urls, limit)

    if not dry_run:
        write_outputs(output_dir, accepted, rejected)

    print(f"input={len(rows)}")
    print(f"already_downloaded_urls={len(downloaded_urls)}")
    print(f"known_bad_urls={len(known_bad_urls)}")
    print(f"accepted={len(accepted)}")
    print(f"rejected={len(rejected)}")
    print(f"limit={limit}")
    print(f"dry_run={str(dry_run).lower()}")
    print(f"urls={output_dir / URLS_OUT}")
    print(f"review_csv={output_dir / REVIEW_OUT}")
    print(f"rejected_csv={output_dir / REJECTED_OUT}")

    return accepted, rejected


def write_test_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        input_csv = root / "filtered_album_candidates.csv"
        manifest_csv = root / "source_manifest.csv"
        known_bad = root / "known_bad_urls.txt"
        output_dir = root / "out"

        write_test_csv(
            input_csv,
            [
                {
                    "artist": "Deftones",
                    "search_query": "Deftones full album official playlist",
                    "url": "https://www.youtube.com/watch?v=downloaded",
                    "title": "Deftones - Around The Fur (Full Album)",
                },
                {
                    "artist": "Loathe",
                    "search_query": "Loathe full album official playlist",
                    "url": "https://www.youtube.com/watch?v=wrongartist",
                    "title": 'WOLFPACK "Loathe" FULL ALBUM STREAM',
                },
                {
                    "artist": "Starset",
                    "search_query": "Starset full album official playlist",
                    "url": "https://youtu.be/accepted",
                    "title": "Starset - Transmissions (Full Album)",
                },
                {
                    "artist": "I Prevail",
                    "search_query": "I Prevail full album official playlist",
                    "url": "https://www.youtube.com/watch?v=knownbad",
                    "title": "SLAUGHTER TO PREVAIL - GRIZZLY (FULL ALBUM)",
                },
                {
                    "artist": "Korn",
                    "search_query": "Korn full album official playlist",
                    "url": "https://www.youtube.com/watch?v=overlimit",
                    "title": "Korn - Korn (Full Album) HQ",
                },
            ],
            INPUT_FIELDS,
        )
        write_test_csv(
            manifest_csv,
            [
                {
                    "url": "https://www.youtube.com/watch?v=downloaded",
                    "status": "success",
                    "notes": "test fixture",
                }
            ],
            ["url", "status", "notes"],
        )
        known_bad.write_text("https://www.youtube.com/watch?v=knownbad\n", encoding="utf-8")

        accepted, rejected = run(input_csv, manifest_csv, known_bad, output_dir, 1, dry_run=False)
        reasons = {row["url"]: row["reject_reason"] for row in rejected}

        assert [row["url"] for row in accepted] == ["https://www.youtube.com/watch?v=accepted"]
        assert reasons["https://www.youtube.com/watch?v=downloaded"] == "already_downloaded"
        assert reasons["https://www.youtube.com/watch?v=wrongartist"] == "missing_artist_signal"
        assert reasons["https://www.youtube.com/watch?v=knownbad"] == "known_bad_url"
        assert reasons["https://www.youtube.com/watch?v=overlimit"] == "over_limit"
        assert (output_dir / URLS_OUT).read_text(encoding="utf-8").strip().endswith("accepted")

    print("self_test=passed")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build reviewed Scarlette Track Library Phase 3 candidate reports."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Filtered discovery CSV.")
    parser.add_argument(
        "--manifest",
        type=Path,
        default=DEFAULT_MANIFEST,
        help="Scarlette source manifest CSV; missing file is allowed.",
    )
    parser.add_argument(
        "--known-bad",
        type=Path,
        default=DEFAULT_KNOWN_BAD_URLS,
        help="Plain-text URL denylist.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--dry-run", action="store_true", help="Validate and print counts without writing reports.")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic local fixture validation.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()

    run(args.input, args.manifest, args.known_bad, args.output_dir, args.limit, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

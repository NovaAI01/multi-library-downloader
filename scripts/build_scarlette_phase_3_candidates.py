#!/usr/bin/env python3

from __future__ import annotations

import argparse
import csv
import tempfile
import unicodedata
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import filter_scarlette_album_candidates as candidate_filter

DEFAULT_INPUT = Path("reports/scarlette_discovery/candidate_album_urls.csv")
DEFAULT_OUTPUT_DIR = Path("reports/scarlette_track_phase_3")
DEFAULT_MANIFEST = Path.home() / "Music/ScarletteTrackLibrary/_manifests/source_manifest.csv"
DEFAULT_KNOWN_BAD_URLS = Path("config/scarlette_known_bad_urls.txt")
DEFAULT_LICENSED_ARTISTS = Path("config/scarlette_licensed_artists.txt")
DEFAULT_LIMIT = 40

CLEAN_URLS_OUT = "track_phase_3a_clean_urls.txt"
MESSY_URLS_OUT = "track_phase_3a_messy_urls.txt"
REVIEW_OUT = "track_phase_3a_review.csv"
REJECTED_OUT = "track_phase_3a_rejected.csv"

INPUT_FIELDS = ["artist", "search_query", "url", "title"]
REVIEW_FIELDS = [
    "url",
    "artist",
    "title",
    "lane",
    "expected_quality",
    "reason",
    "expected_system_behavior",
]
REJECTED_FIELDS = INPUT_FIELDS + ["reject_reason"]

MESSY_TERMS = {
    "best of": "best-of collection",
    "best songs": "best-of collection",
    "collection": "collection source",
    "full discography": "discography source",
    "full album/song": "album/song source",
    "greatest hits": "best-of collection",
    "hits 2024": "hits collection",
    "mix": "mix source",
    "no guitar": "alternate stem or edit source",
    "outdated": "stale metadata marker",
    "playlist": "playlist source",
    "soundtrack": "soundtrack source",
    "tanpa iklan": "ambiguous no-ads compilation signal",
    "top 10": "ranked hits collection",
    "top 100": "ranked hits collection",
    "top artists": "ranked hits collection",
    "top hits": "ranked hits collection",
    "top songs": "ranked hits collection",
    "tracklist": "tracklist metadata",
    "unplugged": "alternate performance source",
    "visualizer": "video-oriented source",
    "vinyl rip": "rip metadata",
}

UNSAFE_TERMS = {
    "cover": "unsafe_or_unusable:cover",
    "isolated vocals": "unsafe_or_unusable:isolated_vocals",
    "karaoke": "unsafe_or_unusable:karaoke",
    "reaction": "unsafe_or_unusable:reaction",
}


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


def read_licensed_artists(path: Path) -> set[str]:
    if not path.exists():
        return set()

    artists: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            artists.add(candidate_filter.word_norm(value))
    return artists


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
        raise FileNotFoundError(f"missing candidate CSV: {path}")

    with path.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        missing = [field for field in INPUT_FIELDS if field not in fieldnames]
        if missing:
            raise ValueError(f"{path} missing required columns: {', '.join(missing)}")
        return [{field: row.get(field, "") for field in INPUT_FIELDS} for row in reader]


def has_album_signal(title: str) -> bool:
    normalized = candidate_filter.norm(title)
    return any(term in normalized for term in candidate_filter.POSITIVE_TERMS)


def has_stylized_unicode(title: str) -> bool:
    return any(
        ord(char) > 127 and unicodedata.category(char)[0] in {"L", "M", "N"}
        for char in title
    )


def matching_messy_reasons(title: str) -> list[str]:
    normalized = candidate_filter.norm(title)
    return [reason for term, reason in MESSY_TERMS.items() if term in normalized]


def unsafe_reason(title: str) -> str:
    normalized = candidate_filter.norm(title)
    for term, reason in UNSAFE_TERMS.items():
        if term in normalized:
            return reason
    return ""


def review_row(
    row: dict[str, str],
    lane: str,
    expected_quality: str,
    reason: str,
    expected_system_behavior: str,
) -> dict[str, str]:
    return {
        "url": row.get("url", ""),
        "artist": row.get("artist", ""),
        "title": row.get("title", ""),
        "lane": lane,
        "expected_quality": expected_quality,
        "reason": reason,
        "expected_system_behavior": expected_system_behavior,
    }


def rejected_row(row: dict[str, str], reason: str) -> dict[str, str]:
    return {**{field: row.get(field, "") for field in INPUT_FIELDS}, "reject_reason": reason}


def classify_row(row: dict[str, str], title_keys_seen: set[tuple[str, str]]) -> dict[str, str]:
    artist = row.get("artist", "")
    title = row.get("title", "")
    artist_phrase = candidate_filter.word_norm(artist)
    artist_compact = candidate_filter.compact_norm(artist)
    title_words = candidate_filter.word_norm(title)
    title_compact = candidate_filter.compact_norm(title)
    artist_signal = candidate_filter.has_artist_signal(title, artist)
    album_signal = has_album_signal(title)
    messy_reasons = matching_messy_reasons(title)
    title_key = (candidate_filter.word_norm(artist), candidate_filter.word_norm(title))
    duplicate_title = title_key in title_keys_seen

    if has_stylized_unicode(title):
        messy_reasons.append("stylized unicode title")

    if not album_signal:
        messy_reasons.append("missing album signal")

    if not artist_signal:
        messy_reasons.append("ambiguous or conflicting artist/title signal")

    if (
        artist_signal
        and artist_phrase
        and artist_phrase not in f" {title_words} "
        and len(artist_compact) >= 3
        and artist_compact in title_compact
    ):
        messy_reasons.append("stylized artist/title spacing")

    if duplicate_title:
        messy_reasons.append("possible duplicate album title")

    title_keys_seen.add(title_key)

    if not messy_reasons:
        return review_row(row, "clean", "high", "clear artist/title album source", "clean_plan")

    if duplicate_title:
        behavior = "duplicate_candidate"
    elif not artist_signal:
        behavior = "identity_conflict"
    elif not album_signal:
        behavior = "metadata_uncertain"
    else:
        behavior = "needs_review"

    return review_row(row, "messy", "review", "; ".join(dict.fromkeys(messy_reasons)), behavior)


def build_candidates(
    rows: list[dict[str, str]],
    downloaded_urls: set[str],
    known_bad_urls: set[str],
    licensed_artists: set[str],
    limit: int,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    clean: list[dict[str, str]] = []
    messy: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    title_keys_seen: set[tuple[str, str]] = set()

    for row in rows:
        url = canonical_url(row.get("url", ""))
        row = {**row, "url": url}
        artist_key = candidate_filter.word_norm(row.get("artist", ""))

        if not url:
            rejected.append(rejected_row(row, "missing_url"))
            continue

        if not row.get("title", "").strip():
            rejected.append(rejected_row(row, "missing_title"))
            continue

        if licensed_artists and artist_key not in licensed_artists:
            rejected.append(rejected_row(row, "artist_outside_licensed_scope"))
            continue

        if url in seen_urls:
            rejected.append(rejected_row(row, "duplicate_url_in_candidate_input"))
            continue
        seen_urls.add(url)

        if url in downloaded_urls:
            rejected.append(rejected_row(row, "already_downloaded"))
            continue

        if url in known_bad_urls:
            rejected.append(rejected_row(row, "known_bad_or_out_of_scope_url"))
            continue

        reason = unsafe_reason(row.get("title", ""))
        if reason:
            rejected.append(rejected_row(row, reason))
            continue

        classified = classify_row(row, title_keys_seen)
        lane = classified["lane"]

        if lane == "clean":
            if len(clean) >= limit:
                rejected.append(rejected_row(row, "clean_lane_over_limit"))
                continue
            clean.append(classified)
            continue

        if len(messy) >= limit:
            rejected.append(rejected_row(row, "messy_lane_over_limit"))
            continue
        messy.append(classified)

    return clean, messy, rejected


def write_outputs(
    output_dir: Path,
    clean: list[dict[str, str]],
    messy: list[dict[str, str]],
    rejected: list[dict[str, str]],
) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)

    with (output_dir / CLEAN_URLS_OUT).open("w", encoding="utf-8") as f:
        for row in clean:
            f.write(row["url"] + "\n")

    with (output_dir / MESSY_URLS_OUT).open("w", encoding="utf-8") as f:
        for row in messy:
            f.write(row["url"] + "\n")

    with (output_dir / REVIEW_OUT).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REVIEW_FIELDS)
        writer.writeheader()
        writer.writerows(clean + messy)

    with (output_dir / REJECTED_OUT).open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=REJECTED_FIELDS)
        writer.writeheader()
        writer.writerows(rejected)


def run(
    input_csv: Path,
    manifest_csv: Path,
    known_bad_file: Path,
    licensed_artists_file: Path,
    output_dir: Path,
    limit: int,
    dry_run: bool,
) -> tuple[list[dict[str, str]], list[dict[str, str]], list[dict[str, str]]]:
    if limit < 1:
        raise ValueError("--limit must be greater than zero")

    rows = read_candidate_rows(input_csv)
    downloaded_urls = read_manifest_urls(manifest_csv)
    known_bad_urls = read_plain_url_file(known_bad_file)
    licensed_artists = read_licensed_artists(licensed_artists_file)
    clean, messy, rejected = build_candidates(rows, downloaded_urls, known_bad_urls, licensed_artists, limit)

    if not dry_run:
        write_outputs(output_dir, clean, messy, rejected)

    print(f"input={len(rows)}")
    print(f"already_downloaded_urls={len(downloaded_urls)}")
    print(f"known_bad_urls={len(known_bad_urls)}")
    print(f"licensed_artists={len(licensed_artists)}")
    print(f"clean={len(clean)}")
    print(f"messy={len(messy)}")
    print(f"rejected={len(rejected)}")
    print(f"limit_per_lane={limit}")
    print(f"dry_run={str(dry_run).lower()}")
    print(f"clean_urls={output_dir / CLEAN_URLS_OUT}")
    print(f"messy_urls={output_dir / MESSY_URLS_OUT}")
    print(f"review_csv={output_dir / REVIEW_OUT}")
    print(f"rejected_csv={output_dir / REJECTED_OUT}")

    return clean, messy, rejected


def write_test_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def self_test() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        input_csv = root / "candidate_album_urls.csv"
        manifest_csv = root / "source_manifest.csv"
        known_bad = root / "known_bad_urls.txt"
        licensed_artists = root / "licensed_artists.txt"
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
                    "artist": "Starset",
                    "search_query": "Starset full album official playlist",
                    "url": "https://youtu.be/clean",
                    "title": "Starset - Transmissions (Full Album)",
                },
                {
                    "artist": "Loathe",
                    "search_query": "Loathe full album official playlist",
                    "url": "https://www.youtube.com/watch?v=messy",
                    "title": 'WOLFPACK "Loathe" FULL ALBUM STREAM',
                },
                {
                    "artist": "Flyleaf",
                    "search_query": "Flyleaf full album official playlist",
                    "url": "https://www.youtube.com/watch?v=bestof",
                    "title": "Flyleaf Greatest Hits Full Album",
                },
                {
                    "artist": "Unknown Artist",
                    "search_query": "Unknown Artist full album official playlist",
                    "url": "https://www.youtube.com/watch?v=scope",
                    "title": "Unknown Artist - Full Album",
                },
                {
                    "artist": "Korn",
                    "search_query": "Korn full album official playlist",
                    "url": "https://www.youtube.com/watch?v=knownbad",
                    "title": "Korn - Known Broken (Full Album)",
                },
                {
                    "artist": "Korn",
                    "search_query": "Korn full album official playlist",
                    "url": "https://www.youtube.com/watch?v=cover",
                    "title": "Korn - Cover Songs Full Album",
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
        licensed_artists.write_text("Deftones\nStarset\nLoathe\nFlyleaf\nKorn\n", encoding="utf-8")

        clean, messy, rejected = run(
            input_csv,
            manifest_csv,
            known_bad,
            licensed_artists,
            output_dir,
            40,
            dry_run=False,
        )
        rejected_reasons = {row["url"]: row["reject_reason"] for row in rejected}
        messy_behaviors = {row["url"]: row["expected_system_behavior"] for row in messy}

        assert [row["url"] for row in clean] == ["https://www.youtube.com/watch?v=clean"]
        assert messy_behaviors["https://www.youtube.com/watch?v=messy"] == "identity_conflict"
        assert messy_behaviors["https://www.youtube.com/watch?v=bestof"] == "needs_review"
        assert rejected_reasons["https://www.youtube.com/watch?v=downloaded"] == "already_downloaded"
        assert rejected_reasons["https://www.youtube.com/watch?v=scope"] == "artist_outside_licensed_scope"
        assert rejected_reasons["https://www.youtube.com/watch?v=knownbad"] == "known_bad_or_out_of_scope_url"
        assert rejected_reasons["https://www.youtube.com/watch?v=cover"] == "unsafe_or_unusable:cover"
        assert (output_dir / CLEAN_URLS_OUT).read_text(encoding="utf-8").strip().endswith("clean")
        assert (output_dir / MESSY_URLS_OUT).read_text(encoding="utf-8").count("\n") == 2

    print("self_test=passed")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build clean and messy Scarlette Track Library Phase 3 candidate reports."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT, help="Discovery candidate CSV.")
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
        help="Plain-text hard-excluded URL list.",
    )
    parser.add_argument(
        "--licensed-artists",
        type=Path,
        default=DEFAULT_LICENSED_ARTISTS,
        help="Allowed artist-scope file.",
    )
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="Maximum URLs per lane.")
    parser.add_argument("--dry-run", action="store_true", help="Validate and print counts without writing reports.")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic local fixture validation.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.self_test:
        return self_test()

    run(
        args.input,
        args.manifest,
        args.known_bad,
        args.licensed_artists,
        args.output_dir,
        args.limit,
        args.dry_run,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

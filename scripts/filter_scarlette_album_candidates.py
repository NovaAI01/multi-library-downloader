#!/usr/bin/env python3

from __future__ import annotations

import csv
from pathlib import Path

SRC = Path("reports/scarlette_discovery/candidate_album_urls.csv")
OUT = Path("reports/scarlette_discovery/filtered_album_candidates.csv")
URL_OUT = Path("reports/scarlette_discovery/filtered_album_candidate_urls.txt")
REJECTED_OUT = Path("reports/scarlette_discovery/rejected_album_candidates.csv")

POSITIVE_TERMS = [
    "full album",
    "album stream",
    "[full album]",
    "full album stream",
]

NEGATIVE_TERMS = [
    "greatest hits",
    "top 100",
    "top songs",
    "top 10",
    "top hits",
    "best songs",
    "best of",
    "top artists",
    "hits 2024",
    "music video",
    "official video",
    "official music video",
    "visualizer",
    "lyric video",
    "playlist",
    "mix",
    "collection",
    "unplugged",
    "outdated",
    "isolated vocals",
    "karaoke",
    "cover",
    "reaction",
]


def norm(value: str) -> str:
    return " ".join(value.lower().strip().split())


def row_reason(row: dict[str, str]) -> str:
    artist = norm(row.get("artist", ""))
    title = norm(row.get("title", ""))

    if not any(term in title for term in POSITIVE_TERMS):
        return "missing_album_signal"

    for term in NEGATIVE_TERMS:
        if term in title:
            return f"negative_term:{term}"

    if artist == "currents" and "tame impala" in title:
        return "wrong_artist:tame_impala_currents"

    return ""


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"missing source csv: {SRC}")

    OUT.parent.mkdir(parents=True, exist_ok=True)

    kept: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []

    with SRC.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        reason = row_reason(row)
        if reason:
            rejected.append({**row, "reject_reason": reason})
        else:
            kept.append(row)

    fieldnames = ["artist", "search_query", "url", "title"]

    with OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept)

    with URL_OUT.open("w", encoding="utf-8") as f:
        for row in kept:
            f.write(row["url"] + "\n")

    with REJECTED_OUT.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames + ["reject_reason"])
        writer.writeheader()
        writer.writerows(rejected)

    print(f"input={len(rows)}")
    print(f"kept={len(kept)}")
    print(f"rejected={len(rejected)}")
    print(f"csv={OUT}")
    print(f"urls={URL_OUT}")
    print(f"rejected_csv={REJECTED_OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

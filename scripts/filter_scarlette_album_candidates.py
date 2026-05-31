#!/usr/bin/env python3

from __future__ import annotations

import csv
import re
import unicodedata
from pathlib import Path

SRC = Path("reports/scarlette_discovery/candidate_album_urls.csv")
OUT = Path("reports/scarlette_discovery/filtered_album_candidates.csv")
URL_OUT = Path("reports/scarlette_discovery/filtered_album_candidate_urls.txt")
REJECTED_OUT = Path("reports/scarlette_discovery/rejected_album_candidates.csv")
KNOWN_BAD_URLS = Path("config/scarlette_known_bad_urls.txt")

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
    "soundtrack",
    "no guitar",
    "full album/song",
    "tracklist",
    "vinyl rip",
    "tanpa iklan",
]

ARTIST_ALIASES = {
    "rage against the machine": ["ratm"],
    "system of a down": ["soad"],
}


def norm(value: str) -> str:
    return " ".join(value.lower().strip().split())


def ascii_fold(value: str) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(char)
    )


def word_norm(value: str) -> str:
    folded = ascii_fold(value).lower()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", folded).split())


def compact_norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", ascii_fold(value).lower())


def leading_artist_match(title: str, artist_phrase: str, artist_compact: str) -> bool:
    title_words = word_norm(title)
    title_compact = compact_norm(title)

    return title_words.startswith(f"{artist_phrase} ") or title_words == artist_phrase or (
        len(artist_compact) >= 3 and title_compact.startswith(artist_compact)
    )


def has_artist_signal(title: str, artist: str) -> bool:
    artist_phrase = word_norm(artist)
    artist_compact = compact_norm(artist)
    title_words = word_norm(title)
    title_compact = compact_norm(title)

    if not artist_phrase or not title_words:
        return False

    artist_word_count = len(artist_phrase.split())

    # One-word artist names are common album titles and search false positives;
    # require the title to begin with the requested artist credit.
    if artist_word_count == 1:
        return leading_artist_match(title, artist_phrase, artist_compact)

    padded_title = f" {title_words} "
    if f" {artist_phrase} " in padded_title:
        return True

    if len(artist_compact) >= 6 and artist_compact in title_compact:
        return True

    for alias in ARTIST_ALIASES.get(artist_phrase, []):
        alias_phrase = word_norm(alias)
        alias_compact = compact_norm(alias)
        if f" {alias_phrase} " in padded_title:
            return True
        if len(alias_compact) >= 3 and title_compact.startswith(alias_compact):
            return True

    return False


def read_url_set(path: Path) -> set[str]:
    if not path.exists():
        return set()

    urls: set[str] = set()
    with path.open(encoding="utf-8") as f:
        for line in f:
            value = line.strip()
            if not value or value.startswith("#"):
                continue
            urls.add(value)
    return urls


def row_reason(row: dict[str, str], known_bad_urls: set[str] | None = None) -> str:
    known_bad_urls = known_bad_urls or set()
    url = row.get("url", "").strip()
    artist = norm(row.get("artist", ""))
    title = norm(row.get("title", ""))

    if not url:
        return "missing_url"

    if url in known_bad_urls:
        return "known_bad_url"

    if not title:
        return "missing_title"

    if not any(term in title for term in POSITIVE_TERMS):
        return "missing_album_signal"

    for term in NEGATIVE_TERMS:
        if term in title:
            return f"negative_term:{term}"

    if not has_artist_signal(row.get("title", ""), row.get("artist", "")):
        return "missing_artist_signal"

    if artist == "currents" and "tame impala" in title:
        return "wrong_artist:tame_impala_currents"

    return ""


def main() -> int:
    if not SRC.exists():
        raise SystemExit(f"missing source csv: {SRC}")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    known_bad_urls = read_url_set(KNOWN_BAD_URLS)

    kept: list[dict[str, str]] = []
    rejected: list[dict[str, str]] = []

    with SRC.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    for row in rows:
        reason = row_reason(row, known_bad_urls)
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

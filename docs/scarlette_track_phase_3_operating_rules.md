# Scarlette Track Library Phase 3 Operating Rules

## Scope

Phase 3 expands the active proof library from the Phase 2 baseline of 113 individual
track files toward 500 tracks.

Active proof library:

```text
~/Music/ScarletteTrackLibrary
```

Deprecated library:

```text
~/Music/ScarletteTestLibrary
```

Do not use the deprecated library for Phase 3 proof work.

## Governance Gate

Phase 3 candidates must pass a report-only review step before any download batch is
prepared. The review step intentionally preserves realistic messy candidates so the
Music Library Intelligence Platform can be tested against metadata conflicts, duplicate
signals, stylized titles, and low-quality folder/metadata inputs.

Required candidate path:

1. Run metadata-only discovery with `scripts/discover_scarlette_album_candidates.sh`.
2. Run `scripts/build_scarlette_phase_3_candidates.py`.
3. Manually review `reports/scarlette_track_phase_3/track_phase_3a_review.csv`.
4. Promote only operator-approved URLs into a download URL file.

`scripts/filter_scarlette_album_candidates.py` remains available for clean-only
exploration, but it is not the Phase 3 governance input because it removes messy
cases that are useful for platform testing.

The Phase 3 builder reads:

```text
reports/scarlette_discovery/candidate_album_urls.csv
~/Music/ScarletteTrackLibrary/_manifests/source_manifest.csv
config/scarlette_known_bad_urls.txt
config/scarlette_licensed_artists.txt
```

It writes ignored reports only:

```text
reports/scarlette_track_phase_3/track_phase_3a_clean_urls.txt
reports/scarlette_track_phase_3/track_phase_3a_messy_urls.txt
reports/scarlette_track_phase_3/track_phase_3a_review.csv
reports/scarlette_track_phase_3/track_phase_3a_rejected.csv
```

Default candidate limit is 40 per lane. Use `--limit N` for a smaller or larger
clean and messy review batch.

## Review Lanes

Clean lane candidates have:

- clear artist/title match
- album or chapter-splittable source signal
- low ambiguity

Messy lane candidates are retained for expected failure or review testing when they
show:

- ambiguous uploader/title signal
- stylized Unicode titles
- best-of, playlist, mix, or collection language
- possible duplicate albums
- mixed folder or metadata quality
- wrong-looking but useful identity-conflict signals

The review CSV uses these columns:

```text
url,artist,title,lane,expected_quality,reason,expected_system_behavior
```

Expected system behavior values include:

- `clean_plan`
- `needs_review`
- `identity_conflict`
- `duplicate_candidate`
- `metadata_uncertain`

## Hard Rejection Rules

The automated gate rejects only when:

- the URL is already present in the active library source manifest
- the URL is listed in `config/scarlette_known_bad_urls.txt` as broken, outside
  licensed scope, or otherwise unusable
- the candidate search artist is outside `config/scarlette_licensed_artists.txt`
- the title or URL is missing
- the source is unsafe or unusable for this test lane, such as cover, karaoke,
  isolated-vocal, or reaction content
- the exact URL is duplicated in the current candidate input

Best-of collections, ambiguous artist/title signals, stylized Unicode, possible
duplicate albums, and metadata-poor sources belong in the messy lane rather than the
rejected file unless they also hit one of the hard rejection rules.

Candidates beyond the requested lane `--limit` are omitted from the current batch with
an over-limit reason; they are not a source-boundary rejection.

## Operating Limits

Do not run audio downloads during candidate generation.

Do not write audio during candidate generation.

Do not run placement, quarantine, or restore commands during Phase 3 collection
proofing.

Do not commit generated files under `reports/`, `logs/`, `archive/`, or downloaded
media files.

The Scarlette download wrapper removes leftover source containers and temporary
files such as `.webm`, `.mp4`, `.mkv`, `.part`, `.ytdl`, `.temp`, and `.tmp`
only when accepted converted audio exists in the same output directory. It does
not clean `_manifests`, and it must not be replaced with ad hoc deletion of the
proof library.

Use the builder dry run or self test for deterministic validation:

```bash
python3 scripts/build_scarlette_phase_3_candidates.py --dry-run
python3 scripts/build_scarlette_phase_3_candidates.py --self-test
```

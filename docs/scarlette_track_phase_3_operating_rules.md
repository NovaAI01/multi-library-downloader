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
prepared.

Required candidate path:

1. Run metadata-only discovery with `scripts/discover_scarlette_album_candidates.sh`.
2. Run `scripts/filter_scarlette_album_candidates.py`.
3. Run `scripts/build_scarlette_phase_3_candidates.py`.
4. Manually review `reports/scarlette_track_phase_3/track_phase_3a_review.csv`.
5. Promote only operator-approved URLs into a download URL file.

The Phase 3 builder reads:

```text
reports/scarlette_discovery/filtered_album_candidates.csv
~/Music/ScarletteTrackLibrary/_manifests/source_manifest.csv
config/scarlette_known_bad_urls.txt
```

It writes ignored reports only:

```text
reports/scarlette_track_phase_3/track_phase_3a_clean_urls.txt
reports/scarlette_track_phase_3/track_phase_3a_review.csv
reports/scarlette_track_phase_3/track_phase_3a_rejected.csv
```

Default candidate limit is 40. Use `--limit N` for a smaller or larger review batch.

## Rejection Rules

The automated gate rejects candidates when:

- the URL is already present in the active library source manifest
- the URL is listed in `config/scarlette_known_bad_urls.txt`
- the candidate URL is duplicated in the current input
- the title lacks an album signal
- the title contains playlist, hits, video, soundtrack, cover, karaoke, or similar negative terms
- the title does not clearly credit the requested artist
- the candidate is beyond the requested `--limit`

One-word artist names require a leading artist credit in the title because they are
frequent wrong-artist or album-title false positives.

## Operating Limits

Do not run audio downloads during candidate generation.

Do not write audio during candidate generation.

Do not run placement, quarantine, or restore commands during Phase 3 collection
proofing.

Do not commit generated files under `reports/`, `logs/`, `archive/`, or downloaded
media files.

Use the builder dry run or self test for deterministic validation:

```bash
python3 scripts/build_scarlette_phase_3_candidates.py --dry-run
python3 scripts/build_scarlette_phase_3_candidates.py --self-test
```

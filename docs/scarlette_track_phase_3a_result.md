# Scarlette Track Library Phase 3A Result

## Result

Phase 3A passed as a mixed clean/messy evidence run.

The goal was not a perfectly clean scan. The goal was to expand the library while proving that messy-source inputs expose real weaknesses in the Music Library Intelligence Platform.

## Target library

~/Music/ScarletteTrackLibrary

## Download proof

- Input URL file: reports/scarlette_track_phase_3/track_phase_3a_mixed_urls.txt
- Selected URL manifest: ~/Music/ScarletteTrackLibrary/_manifests/phase_3a_selected_urls.csv
- Requested URLs: 35
- Successful URLs: 35
- Failed URLs: 0
- Audio files after Phase 3A: 284 reported by downloader summary
- Audio files seen by scan: 285

## Music pipeline proof

- scan_run_id: 7
- total_files_seen: 289
- audio_files_seen: 285
- files_failed: 0
- identified: 284
- partial: 0
- conflicting: 1
- classified: 278
- uncertain: 7
- placement planned: 278
- blocked_unknown_classification: 6
- placement conflicts: 1

## Problem classes exposed

### Unknown classification

Six rows were blocked because classification was uncertain.

Observed causes:

- uploader/channel treated as probable artist
- feature-credit artist names treated as artist identity
- source genre tags only provided generic values such as Music or People & Blogs

Examples:

- NOTHING MORE ft Chris Daughtry — FREEFALL
- NOTHING MORE ft. Sinizter — STUCK
- CT MUSIC — MOTIONLESS IN WHITE | SCORING THE END OF THE WORLD FULL ALBUM 2022
- Ed Bas — Three days grace One X Full Album
- Hits Songs Lyrics — System Of A Down 2024 Greatest Hits
- Melodic Dreams — S.y.s.t.e.m o.f a D.o.w.n Greatest Hits

### Identity conflict

One row created an identity conflict:

- HUB Music — SOAD Greatest Hits Full Album - Best Songs Of SOAD Playlist 2023

Observed reason:

- tag title conflicted with filename title
- uploader/channel metadata overpowered intended artist evidence

## Interpretation

This is useful evidence, not bad collection.

Clean-lane files continued to scan and plan successfully.

Messy-lane files exposed realistic weaknesses around:

- uploader-folder noise
- generic YouTube genre tags
- feature-credit parsing
- greatest-hits collection titles
- stylised artist/title variants
- tag-title versus filename-title conflict handling

## Current rule

Keep clean and messy lanes.

Do not over-filter messy sources. Label them and preserve the expected behaviour in manifests.

Do not run execute-placement, quarantine-duplicates, or restore-quarantine during collection proof phases.

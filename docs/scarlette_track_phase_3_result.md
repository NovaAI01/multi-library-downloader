# Scarlette Track Library Phase 3 Result

## Result

Phase 3 reached the 500-track scale gate and exposed real messy-library weaknesses.

## Target library

~/Music/ScarletteTrackLibrary

## Download proof

- Audio files after final top-up: 535 reported by downloader summary
- Audio files seen by scan: 536
- Download failures in final top-up: 0
- Active archive: archive/scarlette_track_phase_1_archive.txt
- Manifest folder: ~/Music/ScarletteTrackLibrary/_manifests

## Music pipeline proof

- scan_run_id: 8
- total_files_seen: 540
- audio_files_seen: 536
- files_failed: 0
- identified: 480
- partial: 0
- conflicting: 56
- classified: 467
- uncertain: 69
- placement planned: 467
- blocked_unknown_classification: 13
- placement conflicts: 56

## Interpretation

The system can physically scan and process a 500+ track library without file read failures.

The failure mode is semantic, not filesystem-level.

The messy lane exposed realistic weaknesses around identity, classification, and placement governance.

## Dominant root cause

Most placement conflicts are not unrelated failures.

They are concentrated around one messy source:

Eysonance/Holding Absence [Full Album]

Observed pattern:

- tag artist: Eysonance
- tag title: Holding Absence [Full Album]
- chapter filename: actual song title
- system selected embedded tag title over chapter filename evidence
- result: repeated tag_title_conflicts_with_filename_title

## Root cause classes

### 1. Uploader/channel treated as artist

Examples:

- Eysonance
- CT MUSIC
- Ed Bas
- Good Music
- HUB Music
- Hits Music
- Hits Songs Lyrics
- Melodic Dreams

Required future fix:

- detect uploader/channel-like artist evidence
- downgrade uploader evidence when parent folder/title contains a licensed artist
- prefer chapter filename evidence for chapter-split tracks

### 2. Generic source genres

Examples:

- Music
- People & Blogs

Required future fix:

- treat generic source genres as weak evidence
- add fallback classification based on artist seed, folder context, and known library cohort

### 3. Chapter filename versus embedded tag conflict

Observed in chapter-split album downloads.

Required future fix:

- when filename is numbered chapter format, treat filename title as primary track title
- treat embedded full-album title as album evidence, not track title evidence

### 4. Feature-credit parsing

Examples:

- NOTHING MORE ft Chris Daughtry
- NOTHING MORE ft. Sinizter

Required future fix:

- extract lead artist before classification
- preserve featuring artist separately

### 5. Messy best-of collections

Examples:

- SOAD Greatest Hits
- Flyleaf Greatest Hits
- The Pretty Reckless hit playlist

Required future fix:

- route best-of collections to review or compilation handling
- avoid clean placement unless artist/title confidence is strong

## Current gate decision

Do not expand to 1,000 or 5,000 yet.

Next mandate is system hardening against the observed Phase 3 weaknesses.

Do not run execute-placement, quarantine-duplicates, or restore-quarantine during collection proof phases.

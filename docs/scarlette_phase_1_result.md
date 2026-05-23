# Scarlette Test Library Phase 1 Result

## Result

Phase 1 passed with one controlled exception.

## Download proof

- Target folder: ~/Music/ScarletteTestLibrary
- Audio files collected: 25
- Requested URLs: 25
- Successful URLs: 25
- Failed URLs: 0
- Manifest folder: ~/Music/ScarletteTestLibrary/_manifests

## Music pipeline proof

- scan_run_id: 3
- total_files_seen: 28
- audio_files_seen: 25
- files_failed: 0
- identified: 24
- conflicting: 1
- classified: 24
- uncertain: 1
- planned: 24
- placement conflicts: 1

## Known conflict

File:

/home/jack/Music/ScarletteTestLibrary/RockDuk 락덬/[Full Album] N̲ine I̲nch N̲ails - d̲ownw̲ard sp̲iral/ [Full Album] N̲ine I̲nch N̲ails - d̲ownw̲ard sp̲iral.flac

Reason:

- identity_status: conflicting
- classification_status: uncertain
- placement_status: conflict
- placement_confidence: 0.0

Likely cause:

- uploader folder was treated as artist evidence
- stylised Unicode text affected canonical artist/title parsing

## Phase 2 rule

Exclude the Nine Inch Nails candidate URL from the 100-track expansion unless normalization/parsing is improved first.

Do not run execute-placement, quarantine-duplicates, or restore-quarantine.

## Repository evidence

Downloader wrapper commits:

- 2695320 Add Scarlette licensed test library downloader wrapper
- 27cd960 Add Scarlette licensed artist discovery layer

Generated runtime evidence remains outside Git under:

- reports/scarlette_phase_1/
- ~/Music/ScarletteTestLibrary/_manifests/

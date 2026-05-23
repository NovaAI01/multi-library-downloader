#!/usr/bin/env bash

set -u

readonly DEFAULT_URL_FILE="config/scarlette_licensed_urls.txt"
readonly URL_FILE="${1:-$DEFAULT_URL_FILE}"
readonly OUTPUT_DIR="${SCARLETTE_OUTPUT_DIR:-${HOME}/Music/ScarletteTrackLibrary}"
readonly MANIFEST_DIR="${OUTPUT_DIR}/_manifests"
readonly SOURCE_MANIFEST="${MANIFEST_DIR}/source_manifest.csv"
readonly DOWNLOAD_SUMMARY="${MANIFEST_DIR}/download_summary.json"
readonly LICENSE_NOTES="${MANIFEST_DIR}/license_notes.md"
readonly LOG_FILE="logs/scarlette_test_batch.log"
readonly FAILED_URLS_FILE="logs/scarlette_failed_urls.txt"
readonly ARCHIVE_FILE="${SCARLETTE_ARCHIVE_FILE:-archive/scarlette_archive.txt}"
readonly MAX_TRACKS="${MAX_TRACKS:-25}"

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Error: required command not found: %s\n' "$command_name" >&2
    return 1
  fi

  return 0
}

prepare_directories() {
  mkdir -p logs archive "$OUTPUT_DIR" "$MANIFEST_DIR"
  touch "$LOG_FILE" "$FAILED_URLS_FILE" "$ARCHIVE_FILE"

  if [[ ! -f "$SOURCE_MANIFEST" ]]; then
    printf 'url,status,notes\n' > "$SOURCE_MANIFEST"
  fi

  cat > "$LICENSE_NOTES" <<NOTES
# Scarlette Test Library License Notes

This batch is restricted to URLs manually curated by the operator.

Operator assertion:
- URLs are from artists/sources the operator is licensed/permitted to download and keep.
- No ytsearch queries are allowed.
- No DRM bypass, torrents, unauthorized streaming downloads, or unclear sources are allowed.
- Audio is written outside Git to: ${OUTPUT_DIR}

This file records the operating boundary for the local test library.
NOTES
}

load_urls() {
  local url_file="$1"
  local -n loaded_urls_ref="$2"
  local line

  if [[ ! -f "$url_file" ]]; then
    printf 'Error: URL file not found: %s\n' "$url_file" >&2
    return 1
  fi

  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line#"${line%%[![:space:]]*}"}"
    line="${line%"${line##*[![:space:]]}"}"

    [[ -z "$line" ]] && continue
    [[ "$line" == \#* ]] && continue

    if [[ "$line" == ytsearch* ]]; then
      printf 'Error: ytsearch is not allowed in this controlled batch: %s\n' "$line" >&2
      return 1
    fi

    loaded_urls_ref+=("$line")
  done < "$url_file"

  if [[ "${#loaded_urls_ref[@]}" -eq 0 ]]; then
    printf 'Error: URL file contains no usable URLs: %s\n' "$url_file" >&2
    return 1
  fi

  return 0
}

count_audio_files() {
  find "$OUTPUT_DIR" -type f \( -iname "*.mp3" -o -iname "*.flac" -o -iname "*.wav" -o -iname "*.m4a" -o -iname "*.ogg" \) 2>/dev/null | wc -l
}

download_url() {
  local url="$1"

  yt-dlp \
    --extract-audio \
    --audio-format flac \
    --embed-metadata \
    --embed-thumbnail \
    --convert-thumbnails jpg \
    --split-chapters \
    --retries 5 \
    --fragment-retries 5 \
    --retry-sleep 5 \
    --download-archive "$ARCHIVE_FILE" \
    --playlist-end "$MAX_TRACKS" \
    --newline \
    --progress \
    --output "${OUTPUT_DIR}/%(album_artist,artist,uploader|Unknown Artist)s/%(album,title|Unknown Album)s/%(playlist_index|)s %(title)s.%(ext)s" \
    --output "chapter:${OUTPUT_DIR}/%(album_artist,artist,uploader|Unknown Artist)s/%(title)s/%(section_number)02d %(section_title)s.%(ext)s" \
    "$url" 2>&1 | tee -a "$LOG_FILE"

  find "$OUTPUT_DIR" -type d \
    | while IFS= read -r candidate_dir; do
        if find "$candidate_dir" -maxdepth 1 -type f -name "[0-9][0-9] *.flac" | grep -q .; then
          find "$candidate_dir" -maxdepth 1 -type f -iname "*.flac" ! -name "[0-9][0-9] *.flac" -delete
        fi
      done
}

write_summary() {
  local requested_urls="$1"
  local success_count="$2"
  local failed_count="$3"
  local audio_count="$4"

  cat > "$DOWNLOAD_SUMMARY" <<SUMMARY
{
  "target_folder": "${OUTPUT_DIR}",
  "manifest_folder": "${MANIFEST_DIR}",
  "url_file": "${URL_FILE}",
  "requested_urls": ${requested_urls},
  "successful_urls": ${success_count},
  "failed_urls": ${failed_count},
  "audio_file_count": ${audio_count},
  "max_tracks": ${MAX_TRACKS},
  "source_manifest": "${SOURCE_MANIFEST}",
  "license_notes": "${LICENSE_NOTES}",
  "log_file": "${LOG_FILE}",
  "archive_file": "${ARCHIVE_FILE}"
}
SUMMARY
}

main() {
  local urls=()
  local total=0
  local current=0
  local success_count=0
  local failed_count=0
  local audio_count=0
  local url

  require_command yt-dlp || return 1
  require_command ffmpeg || return 1

  prepare_directories
  load_urls "$URL_FILE" urls || return 1

  total="${#urls[@]}"

  printf 'URL file: %s\n' "$URL_FILE"
  printf 'Output directory: %s\n' "$OUTPUT_DIR"
  printf 'Manifest directory: %s\n' "$MANIFEST_DIR"
  printf 'Max tracks: %s\n\n' "$MAX_TRACKS"

  for url in "${urls[@]}"; do
    current=$((current + 1))
    printf '[%d/%d] Downloading: %s\n' "$current" "$total" "$url"

    if download_url "$url"; then
      success_count=$((success_count + 1))
      printf '"%s",success,"operator asserted licensed/permitted source"\n' "$url" >> "$SOURCE_MANIFEST"
      printf 'Result: success\n\n'
    else
      failed_count=$((failed_count + 1))
      printf '%s\n' "$url" >> "$FAILED_URLS_FILE"
      printf '"%s",failed,"see log file"\n' "$url" >> "$SOURCE_MANIFEST"
      printf 'Result: failed\n\n'
    fi
  done

  audio_count="$(count_audio_files)"
  write_summary "$total" "$success_count" "$failed_count" "$audio_count"

  printf 'Audio files found: %s\n' "$audio_count"
  printf 'Summary written: %s\n' "$DOWNLOAD_SUMMARY"

  if [[ "$failed_count" -gt 0 ]]; then
    printf 'Failed URLs were appended to %s.\n' "$FAILED_URLS_FILE"
    return 1
  fi

  return 0
}

main "$@"

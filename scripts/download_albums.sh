#!/usr/bin/env bash

set -u

readonly DEFAULT_URL_FILE="config/example_urls.txt"
readonly URL_FILE="${1:-$DEFAULT_URL_FILE}"
readonly OUTPUT_DIR="${HOME}/Music/rock_library_albums"
readonly LOG_FILE="logs/music_downloader.log"
readonly FAILED_URLS_FILE="logs/failed_album_urls.txt"
readonly ARCHIVE_FILE="archive/archive.txt"

require_command() {
  local command_name="$1"

  if ! command -v "$command_name" >/dev/null 2>&1; then
    printf 'Error: required command not found: %s\n' "$command_name" >&2
    return 1
  fi

  return 0
}

prepare_directories() {
  mkdir -p config scripts logs archive "$OUTPUT_DIR"
  touch "$LOG_FILE" "$FAILED_URLS_FILE" "$ARCHIVE_FILE"
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

    loaded_urls_ref+=("$line")
  done < "$url_file"

  if [[ "${#loaded_urls_ref[@]}" -eq 0 ]]; then
    printf 'Error: URL file contains no downloadable URLs: %s\n' "$url_file" >&2
    return 1
  fi

  return 0
}

print_progress() {
  local current="$1"
  local total="$2"
  local success_count="$3"
  local failed_count="$4"
  local percentage=$((current * 100 / total))

  printf '[%d/%d] %d%% complete | success: %d | failed: %d\n' \
    "$current" "$total" "$percentage" "$success_count" "$failed_count"
}

download_url() {
  local url="$1"

  yt-dlp \
    --extract-audio \
    --audio-format flac \
    --embed-metadata \
    --embed-thumbnail \
    --convert-thumbnails jpg \
    --retries 10 \
    --fragment-retries 10 \
    --retry-sleep 5 \
    --download-archive "$ARCHIVE_FILE" \
    --output "${OUTPUT_DIR}/%(album_artist,artist,uploader|Unknown Artist)s/%(album,title|Unknown Album)s/%(playlist_index|)s %(title)s.%(ext)s" \
    "$url" >>"$LOG_FILE" 2>&1
}

main() {
  local urls=()
  local total=0
  local current=0
  local success_count=0
  local failed_count=0
  local url

  require_command yt-dlp || return 1
  require_command ffmpeg || return 1
  prepare_directories
  load_urls "$URL_FILE" urls || return 1

  total="${#urls[@]}"

  printf 'URL file: %s\n' "$URL_FILE"
  printf 'Output directory: %s\n' "$OUTPUT_DIR"
  printf 'Log file: %s\n' "$LOG_FILE"
  printf 'Archive file: %s\n\n' "$ARCHIVE_FILE"

  for url in "${urls[@]}"; do
    current=$((current + 1))
    print_progress "$current" "$total" "$success_count" "$failed_count"
    printf 'Downloading: %s\n' "$url"

    if download_url "$url"; then
      success_count=$((success_count + 1))
      printf 'Result: success\n\n'
    else
      failed_count=$((failed_count + 1))
      printf '%s\n' "$url" >>"$FAILED_URLS_FILE"
      printf 'Result: failed\n\n'
    fi
  done

  print_progress "$current" "$total" "$success_count" "$failed_count"
  printf '\nDone. Review %s for details.\n' "$LOG_FILE"

  if [[ "$failed_count" -gt 0 ]]; then
    printf 'Failed URLs were appended to %s.\n' "$FAILED_URLS_FILE"
    return 1
  fi

  return 0
}

main "$@"

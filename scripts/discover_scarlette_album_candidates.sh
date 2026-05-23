#!/usr/bin/env bash

set -u

readonly ARTIST_FILE="${1:-config/scarlette_licensed_artists.txt}"
readonly OUT_DIR="reports/scarlette_discovery"
readonly CANDIDATE_FILE="${OUT_DIR}/candidate_album_urls.txt"
readonly CSV_FILE="${OUT_DIR}/candidate_album_urls.csv"
readonly LOG_FILE="logs/scarlette_discovery.log"
readonly RESULTS_PER_ARTIST="${RESULTS_PER_ARTIST:-3}"

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    printf 'Error: required command not found: %s\n' "$1" >&2
    return 1
  fi
}

prepare_outputs() {
  mkdir -p "$OUT_DIR" logs
  : > "$CANDIDATE_FILE"
  printf 'artist,search_query,url,title\n' > "$CSV_FILE"
  : > "$LOG_FILE"
}

discover_artist() {
  local artist="$1"
  local query="${artist} full album official playlist"
  local encoded_query="ytsearch${RESULTS_PER_ARTIST}:${query}"

  printf 'Discovering: %s\n' "$artist"

  yt-dlp \
    --flat-playlist \
    --skip-download \
    --print "%(webpage_url)s	%(title)s" \
    "$encoded_query" 2>>"$LOG_FILE" |
  while IFS=$'\t' read -r url title; do
    [[ -z "${url:-}" ]] && continue
    printf '%s\n' "$url" >> "$CANDIDATE_FILE"
    printf '"%s","%s","%s","%s"\n' "$artist" "$query" "$url" "${title//\"/\"\"}" >> "$CSV_FILE"
  done
}

main() {
  local artist

  require_command yt-dlp || return 1
  prepare_outputs

  while IFS= read -r artist || [[ -n "$artist" ]]; do
    artist="${artist#"${artist%%[![:space:]]*}"}"
    artist="${artist%"${artist##*[![:space:]]}"}"

    [[ -z "$artist" ]] && continue
    [[ "$artist" == \#* ]] && continue

    discover_artist "$artist"
  done < "$ARTIST_FILE"

  sort -u "$CANDIDATE_FILE" -o "$CANDIDATE_FILE"

  printf '\nCandidate URL file: %s\n' "$CANDIDATE_FILE"
  printf 'Candidate CSV file: %s\n' "$CSV_FILE"
  printf 'Candidate count: '
  wc -l < "$CANDIDATE_FILE"
}

main "$@"

#!/usr/bin/env bash

set -u

CRITICAL_FAILURES=0

have_command() {
  command -v "$1" >/dev/null 2>&1
}

print_command_version() {
  local command_name="$1"
  local label="$2"
  shift 2

  if have_command "$command_name"; then
    printf '%s: %s\n' "$label" "$("$@" 2>/dev/null)"
    return 0
  fi

  printf '%s: missing\n' "$label"
  return 1
}

print_os() {
  if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    printf 'OS: %s\n' "${PRETTY_NAME:-unknown}"
    return 0
  fi

  printf 'OS: unknown\n'
}

check_critical() {
  local command_name="$1"
  local label="$2"

  if have_command "$command_name"; then
    printf 'PASS: %s available\n' "$label"
    return 0
  fi

  printf 'FAIL: %s missing\n' "$label"
  CRITICAL_FAILURES=$((CRITICAL_FAILURES + 1))
  return 1
}

main() {
  printf 'System report\n'
  printf '=============\n'
  print_os
  printf 'bash: %s\n' "${BASH_VERSION:-unknown}"

  if have_command ffmpeg; then
    printf 'ffmpeg: %s\n' "$(ffmpeg -version 2>/dev/null | head -n 1)"
  else
    printf 'ffmpeg: missing\n'
  fi

  print_command_version yt-dlp "yt-dlp" yt-dlp --version

  if have_command shellcheck; then
    printf 'shellcheck: %s\n' "$(shellcheck --version 2>/dev/null | awk -F': ' '/^version:/ {print $2; exit}')"
  else
    printf 'shellcheck: missing\n'
  fi

  print_command_version git "git" git --version
  print_command_version node "node" node --version

  printf '\nDownloader dependency readiness\n'
  printf '===============================\n'
  check_critical bash "bash"
  check_critical ffmpeg "ffmpeg"
  check_critical yt-dlp "yt-dlp"
  check_critical git "git"

  printf '\n'
  if [[ "$CRITICAL_FAILURES" -eq 0 ]]; then
    printf 'Downloader dependencies ready: yes\n'
    return 0
  fi

  printf 'Downloader dependencies ready: no (%d critical issue(s))\n' "$CRITICAL_FAILURES"
  return 1
}

main "$@"

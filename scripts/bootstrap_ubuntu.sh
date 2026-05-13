#!/usr/bin/env bash

set -u

readonly APT_PACKAGES=(
  ffmpeg
  nodejs
  python3-mutagen
  shellcheck
  tree
  curl
)

STATUS_FAILURES=0

mark_pass() {
  printf 'PASS: %s\n' "$1"
}

mark_fail() {
  printf 'FAIL: %s\n' "$1"
  STATUS_FAILURES=$((STATUS_FAILURES + 1))
}

print_fail() {
  printf 'FAIL: %s\n' "$1"
}

have_command() {
  command -v "$1" >/dev/null 2>&1
}

run_apt_install() {
  if ! have_command apt-get; then
    mark_fail "apt-get is not available; this bootstrap script supports Ubuntu/Debian systems"
    return 1
  fi

  printf 'Installing required APT packages: %s\n' "${APT_PACKAGES[*]}"

  if ! sudo apt-get update; then
    mark_fail "apt-get update failed"
    return 1
  fi

  if sudo apt-get install -y --no-install-recommends "${APT_PACKAGES[@]}"; then
    mark_pass "APT packages installed"
    return 0
  fi

  mark_fail "APT package installation failed"
  return 1
}

install_ytdlp() {
  local temp_file
  local install_dir="/usr/local/bin"
  local install_path="${install_dir}/yt-dlp"
  local url="https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp"

  if ! have_command curl; then
    mark_fail "curl is required to install yt-dlp"
    return 1
  fi

  temp_file="$(mktemp "${TMPDIR:-/tmp}/yt-dlp.XXXXXX")"
  if [[ -z "$temp_file" ]]; then
    mark_fail "could not create temporary file for yt-dlp"
    return 1
  fi

  printf 'Installing latest stable yt-dlp from official GitHub release\n'

  if ! curl --fail --location --show-error --silent "$url" --output "$temp_file"; then
    rm -f "$temp_file"
    mark_fail "yt-dlp download failed"
    return 1
  fi

  chmod 0755 "$temp_file"

  if ! "$temp_file" --version >/dev/null 2>&1; then
    rm -f "$temp_file"
    mark_fail "downloaded yt-dlp did not pass version check"
    return 1
  fi

  if sudo install -m 0755 "$temp_file" "$install_path"; then
    rm -f "$temp_file"
    mark_pass "yt-dlp installed to ${install_path}"
    return 0
  fi

  rm -f "$temp_file"
  mark_fail "could not install yt-dlp to ${install_path}"
  return 1
}

check_dependency() {
  local command_name="$1"
  local label="$2"

  if have_command "$command_name"; then
    mark_pass "$label"
    return 0
  fi

  mark_fail "$label"
  return 1
}

print_summary() {
  printf '\nEnvironment summary\n'
  printf '===================\n'

  if [[ -r /etc/os-release ]]; then
    # shellcheck disable=SC1091
    . /etc/os-release
    printf 'OS: %s\n' "${PRETTY_NAME:-unknown}"
  else
    printf 'OS: unknown\n'
  fi

  printf 'Bash: %s\n' "${BASH_VERSION:-unknown}"

  if have_command ffmpeg; then
    printf 'ffmpeg: %s\n' "$(ffmpeg -version 2>/dev/null | head -n 1)"
  else
    printf 'ffmpeg: missing\n'
  fi

  if have_command yt-dlp; then
    printf 'yt-dlp: %s\n' "$(yt-dlp --version 2>/dev/null)"
  else
    printf 'yt-dlp: missing\n'
  fi

  if have_command shellcheck; then
    printf 'shellcheck: %s\n' "$(shellcheck --version 2>/dev/null | awk -F': ' '/^version:/ {print $2; exit}')"
  else
    printf 'shellcheck: missing\n'
  fi

  if have_command git; then
    printf 'git: %s\n' "$(git --version 2>/dev/null)"
  else
    printf 'git: missing\n'
  fi

  if have_command node; then
    printf 'node: %s\n' "$(node --version 2>/dev/null)"
  else
    printf 'node: missing\n'
  fi

  if have_command python3; then
    if python3 -c 'import mutagen' >/dev/null 2>&1; then
      printf 'python3-mutagen: available\n'
    else
      printf 'python3-mutagen: missing\n'
    fi
  else
    printf 'python3-mutagen: missing\n'
  fi
}

main() {
  printf 'Ubuntu environment bootstrap\n'
  printf '============================\n\n'

  run_apt_install

  printf '\nDependency checks\n'
  printf '=================\n'

  check_dependency ffmpeg "ffmpeg"
  check_dependency node "nodejs"

  if have_command python3 && python3 -c 'import mutagen' >/dev/null 2>&1; then
    mark_pass "python3-mutagen"
  else
    mark_fail "python3-mutagen"
  fi

  check_dependency shellcheck "shellcheck"
  check_dependency tree "tree"
  check_dependency curl "curl"
  check_dependency git "git"

  if have_command yt-dlp; then
    mark_pass "yt-dlp"
  else
    print_fail "yt-dlp"
    install_ytdlp
    if have_command yt-dlp; then
      mark_pass "yt-dlp after install"
    else
      mark_fail "yt-dlp after install"
    fi
  fi

  print_summary

  printf '\n'
  if [[ "$STATUS_FAILURES" -eq 0 ]]; then
    printf 'Bootstrap summary: PASS\n'
    return 0
  fi

  printf 'Bootstrap summary: FAIL (%d issue(s))\n' "$STATUS_FAILURES"
  return 1
}

main "$@"

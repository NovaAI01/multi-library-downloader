#!/usr/bin/env bash

set -u

readonly DOWNLOADER_SCRIPT="scripts/download_albums.sh"

main() {
  local shell_files=()
  local failures=0
  local script
  local shellcheck_available=0

  mapfile -d '' -t shell_files < <(find . -type f -name '*.sh' -print0 | sort -z)

  printf 'Bash validation\n'
  printf '===============\n\n'

  if [[ "${#shell_files[@]}" -eq 0 ]]; then
    printf 'FAIL: no .sh files found\n'
    failures=$((failures + 1))
  else
    printf 'Detected %d shell script(s).\n\n' "${#shell_files[@]}"
  fi

  for script in "${shell_files[@]}"; do
    printf 'bash -n %s ... ' "$script"
    if bash -n "$script"; then
      printf 'PASS\n'
    else
      printf 'FAIL\n'
      failures=$((failures + 1))
    fi
  done

  printf '\n'

  if command -v shellcheck >/dev/null 2>&1; then
    shellcheck_available=1
  fi

  if [[ "$shellcheck_available" -eq 1 ]]; then
    for script in "${shell_files[@]}"; do
      printf 'shellcheck %s ... ' "$script"
      if shellcheck "$script"; then
        printf 'PASS\n'
      else
        printf 'FAIL\n'
        failures=$((failures + 1))
      fi
    done
  else
    printf 'SKIP: shellcheck is not installed\n'
  fi

  printf '\n'
  printf 'executable %s ... ' "$DOWNLOADER_SCRIPT"
  if [[ -x "$DOWNLOADER_SCRIPT" ]]; then
    printf 'PASS\n'
  else
    printf 'FAIL\n'
    failures=$((failures + 1))
  fi

  printf '\n'
  if [[ "$failures" -eq 0 ]]; then
    printf 'Validation summary: PASS\n'
    return 0
  fi

  printf 'Validation summary: FAIL (%d issue(s))\n' "$failures"
  return 1
}

main "$@"

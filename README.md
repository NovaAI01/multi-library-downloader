# Multi-Library Downloader

A production-style Bash CLI for downloading lawfully accessed, personal-use audio from manually curated album URLs with `yt-dlp`.

This project is intended for personal media library workflows where you already have the right to access and retain the media you download. It does not bypass access controls, authentication, paywalls, regional restrictions, or platform terms. Use it only with sources and content you are legally permitted to download.

## Features

- Downloads album URLs listed in a plain-text file.
- Converts audio to FLAC for archival-quality local playback.
- Embeds available metadata and thumbnails.
- Tracks completed downloads with a `yt-dlp` archive file.
- Logs downloader output and failed URLs.
- Continues processing after individual URL failures.
- Displays batch progress, percentage complete, success count, and failure count.

## Dependencies

Install the following tools before running the downloader:

- Bash
- `yt-dlp`
- `ffmpeg`

On Debian or Ubuntu systems, `ffmpeg` is commonly available through APT:

```bash
sudo apt install ffmpeg
```

Install `yt-dlp` using the method recommended for your environment. For example:

```bash
python3 -m pip install --user yt-dlp
```

## Usage

Review and edit the default URL file:

```bash
config/example_urls.txt
```

Run the downloader:

```bash
./scripts/download_albums.sh
```

Use a custom URL file:

```bash
./scripts/download_albums.sh path/to/urls.txt
```

The script writes converted audio files to:

```text
~/Music/rock_library_albums
```

Blank lines and comment lines beginning with `#` are ignored.

## Validation

Run the local validation script before committing changes:

```bash
./scripts/validate.sh
```

The validator checks Bash syntax, runs `shellcheck` when it is installed, and verifies that the downloader script is executable. GitHub Actions also validates pushes and pull requests automatically.

## Logging And Archive Behavior

All `yt-dlp` output is appended to:

```text
logs/music_downloader.log
```

Failed URLs are appended to:

```text
logs/failed_album_urls.txt
```

Downloaded media IDs are tracked in:

```text
archive/archive.txt
```

The archive file allows reruns to skip items that `yt-dlp` has already completed. The `logs/` and `archive/` directories are ignored by Git except for their `.gitkeep` files, so runtime logs and local archive state stay out of version control.

## Limitations

- This tool depends on source availability and `yt-dlp` extractor support.
- Some platforms may block requests, rate-limit clients, require authentication, or return HTTP 403 responses.
- Metadata and thumbnail quality depend on what the source provides.
- The script does not manage credentials, cookies, VPNs, proxies, or DRM-protected media.
- It is not a general-purpose media organizer; it downloads and converts audio into a fixed local output directory.

## Lawful Use

Only download media you are permitted to access, copy, and keep for personal use. You are responsible for following applicable laws, platform terms, and rights-holder restrictions.

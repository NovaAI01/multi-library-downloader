# Operating Notes

## Workflow

1. Add album URLs to `config/example_urls.txt`, or create a separate URL file.
2. Run `./scripts/download_albums.sh` for the default file.
3. Run `./scripts/download_albums.sh path/to/urls.txt` for a custom file.
4. Review `logs/music_downloader.log` after a run.
5. Review `logs/failed_album_urls.txt` for URLs that need manual follow-up.

Downloaded and converted audio is written to:

```text
~/Music/rock_library_albums
```

## Manual URL Curation

URLs are kept in a manually curated text file so the operator can verify that each source is appropriate for lawful personal use before it is downloaded. This also keeps the tool predictable: it processes only the URLs explicitly provided by the user and does not crawl, search, scrape, or discover media automatically.

Blank lines and comment lines beginning with `#` are ignored, which makes it safe to annotate batches.

## HTTP 403 Handling

HTTP 403 responses usually mean the source rejected the request. Common causes include expired links, regional restrictions, authentication requirements, rate limits, source-side blocking, or platform policy changes.

The script uses conservative retry settings:

```text
--retries 10
--fragment-retries 10
--retry-sleep 5
```

If a URL still fails, the script continues with the rest of the batch and appends the failed URL to `logs/failed_album_urls.txt`. Review the log before retrying. Do not try to bypass access controls or download content you are not permitted to keep.

## Rerun Behavior

Completed downloads are tracked by `yt-dlp` in:

```text
archive/archive.txt
```

When the script is rerun, `yt-dlp` uses that archive to skip media it has already downloaded. This makes reruns useful after temporary failures: keep the same URL file, rerun the command, and only missing items should be attempted again.

Runtime files in `logs/` and `archive/` are intentionally excluded from Git. The `.gitkeep` files preserve the directories in a clean checkout.

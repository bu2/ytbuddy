# ytbuddy

This repository contains helper scripts for working with YouTube channels.

- `fetch_videos.py` retrieves the list of video URLs from a channel.
- `fetch_metadata.py` outputs the full metadata for every video in a channel as
  JSON.

## Requirements

- Python 3.7+
- Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

This installs [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) along with `pytest` and `flake8` for
development tasks.

## Usage

Run the scripts with a channel URL. They accept URLs that include the
`/videos` segment or just the channel root URL.

```bash
python fetch_videos.py https://www.youtube.com/@sequoiacapital/videos
python fetch_metadata.py https://www.youtube.com/@sequoiacapital
```

`fetch_videos.py` prints each video URL on a separate line, while
`fetch_metadata.py` prints a JSON array containing the metadata objects for all
videos.

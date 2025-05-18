# ytbuddy

This repository contains a helper script for working with YouTube channels.

- `fetch.py` can print the list of video URLs or output the full metadata for
  every video in a channel as JSON.

## Requirements

- Python 3.7+
- Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

This installs [`yt-dlp`](https://github.com/yt-dlp/yt-dlp) along with `pytest` and `flake8` for
development tasks.

## Usage

Run the script with a channel URL. It accepts URLs that include the `/videos`
segment or just the channel root URL.

```bash
# Print all video URLs
python fetch.py videos https://www.youtube.com/@sequoiacapital/videos

# Print metadata for all videos
python fetch.py metadata https://www.youtube.com/@sequoiacapital
```

The ``videos`` command prints each video URL on a separate line, while the
``metadata`` command prints a JSON array containing the metadata objects for all
videos. When running ``metadata``, the JSON output is also saved to a file named
``metadata.json`` in the current directory.

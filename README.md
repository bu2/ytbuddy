# ytbuddy

This repository contains a helper script `fetch_videos.py` that retrieves the
list of video URLs from a YouTube channel.

## Requirements

- Python 3.7+
- Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

This installs [`pytube`](https://pytube.io/) along with `pytest` and `flake8` for
development tasks.

## Usage

Run the script with a channel URL. It accepts URLs that include the `/videos`
segment or just the channel root URL.

```bash
python fetch_videos.py https://www.youtube.com/@sequoiacapital/videos
```

The script outputs the URLs of the videos on the channel, one per line.

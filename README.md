# ytbuddy

This repository contains a helper script for working with YouTube channels.

- `app.py` can print the list of video URLs or output the full metadata for
  every video in a channel as JSON.  Running it with Streamlit provides a simple
  web UI for fetching metadata interactively.

## Requirements

- Python 3.7+
- Install dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

This installs [`yt-dlp`](https://github.com/yt-dlp/yt-dlp),
[`ray`](https://github.com/ray-project/ray), and the `pytest` and `flake8` tools
used for development tasks.

## Usage

Run the script with a channel URL. It accepts URLs that include the `/videos`
segment or just the channel root URL.

```bash
# Print all video URLs
python app.py videos https://www.youtube.com/@sequoiacapital/videos

# Print metadata for all videos (parallelized with Ray)
python app.py metadata https://www.youtube.com/@sequoiacapital

# Launch the web UI
streamlit run app.py
```

Fetching metadata runs multiple workers using Ray so downloads happen concurrently.

The ``videos`` command prints each video URL on a separate line, while the
``metadata`` command prints a JSON array containing the metadata objects for all
videos. When running ``metadata``, the JSON output is also saved to a file named
``metadata.json`` in the current directory.

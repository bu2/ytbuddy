#!/usr/bin/env python3
"""Interactively fetch YouTube video URLs and metadata.

This module exposes the same helpers as ``fetch.py`` but also provides a
Streamlit UI.  The original command line interface is still available and can
be invoked with::

    python app.py videos CHANNEL_URL
    python app.py metadata CHANNEL_URL

Running ``streamlit run app.py`` will launch the web interface.
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any, Dict, List

import ray

from yt_dlp import YoutubeDL


# --- Helpers ---------------------------------------------------------------

def _normalize_channel_url(url: str) -> str:
    """Return a canonical *Videos*-tab URL for the channel."""
    if url.rstrip("/").endswith("/videos"):
        return url.rstrip("/")

    m = re.match(r"(https?://www\.youtube\.com/[^/]+)", url)
    if not m:
        raise ValueError(f"Unrecognized YouTube URL: {url}")
    return m.group(1) + "/videos"


def fetch_video_urls(channel_url: str) -> List[str]:
    """Return list of video URLs for the channel using ``yt-dlp``."""
    ydl_opts = {
        "extract_flat": "in_playlist",
        "skip_download": True,
        "quiet": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(channel_url, download=False)
    urls: List[str] = []
    for entry in info.get("entries", []):
        url = entry.get("url")
        if not url:
            continue
        if not url.startswith("http"):
            url = f"https://www.youtube.com/watch?v={url}"
        urls.append(url)
    return urls


def fetch_video_metadata(video_url: str) -> Dict[str, Any]:
    """Return metadata for a single YouTube video."""
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
    return info


@ray.remote
def _fetch_video_metadata_remote(video_url: str) -> Dict[str, Any]:
    """Ray remote wrapper for :func:`fetch_video_metadata`."""
    return fetch_video_metadata(video_url)


def fetch_all_metadata(channel_url: str) -> List[Dict[str, Any]]:
    """Return metadata for all videos on the channel."""
    channel_root = _normalize_channel_url(channel_url)
    video_urls = fetch_video_urls(channel_root)

    ray.init(ignore_reinit_error=True)
    try:
        refs = [_fetch_video_metadata_remote.remote(url) for url in video_urls]
        metadata = ray.get(refs)
    finally:
        ray.shutdown()

    return metadata


def fetch_metadata_stream(channel_url: str):
    """Yield metadata for all channel videos as each item becomes available."""
    channel_root = _normalize_channel_url(channel_url)
    video_urls = fetch_video_urls(channel_root)

    ray.init(ignore_reinit_error=True)
    try:
        refs = [_fetch_video_metadata_remote.remote(url) for url in video_urls]
        remaining = refs
        while remaining:
            done, remaining = ray.wait(remaining)
            yield ray.get(done[0])
    finally:
        ray.shutdown()


# --- CLI ------------------------------------------------------------------

def _usage() -> str:
    return (
        "Usage:\n"
        "    python app.py videos CHANNEL_URL\n"
        "    python app.py metadata CHANNEL_URL\n"
        "    streamlit run app.py"
    )


def main(args: List[str]) -> None:
    if len(args) != 2 or args[0] not in {"videos", "metadata"}:
        print(_usage())
        raise SystemExit(1)

    action, channel_url = args
    channel_root = _normalize_channel_url(channel_url)

    if action == "videos":
        for video_url in fetch_video_urls(channel_root):
            print(video_url)
    else:  # metadata
        all_metadata = fetch_all_metadata(channel_root)
        print(json.dumps(all_metadata, indent=2))
        with open("metadata.json", "w", encoding="utf-8") as fp:
            json.dump(all_metadata, fp, indent=2)


def run_streamlit() -> None:
    """Launch the Streamlit UI."""
    import streamlit as st

    st.title("YouTube Metadata Fetcher")

    channel_url = st.text_input("YouTube Channel URL")

    if st.button("Fetch Metadata") and channel_url:
        st.write("Fetching video list...")
        video_urls = fetch_video_urls(channel_url)
        st.write(f"Found {len(video_urls)} videos.")

        progress_bar = st.progress(0)
        status = st.empty()
        metadata: List[Dict[str, Any]] = []

        for i, info in enumerate(fetch_metadata_stream(channel_url), start=1):
            metadata.append(info)
            progress_bar.progress(i / len(video_urls))
            status.write(f"Fetched {i}/{len(video_urls)}: {info.get('title')}")

        with open("metadata.json", "w", encoding="utf-8") as fp:
            json.dump(metadata, fp, indent=2)
        st.success("Done fetching metadata")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        run_streamlit()

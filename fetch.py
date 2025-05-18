#!/usr/bin/env python3
"""Fetch videos or metadata from a YouTube channel.

This script combines the functionality of ``fetch_videos.py`` and
``fetch_metadata.py``.

Usage::

    python fetch.py videos CHANNEL_URL
    python fetch.py metadata CHANNEL_URL
"""

from __future__ import annotations

import json
import re
import sys
from typing import Any, Dict, List

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


def fetch_all_metadata(channel_url: str) -> List[Dict[str, Any]]:
    """Return metadata for all videos on the channel."""
    channel_root = _normalize_channel_url(channel_url)
    metadata = []
    for url in fetch_video_urls(channel_root):
        metadata.append(fetch_video_metadata(url))
    return metadata


# --- CLI ------------------------------------------------------------------

def _usage() -> str:
    return (
        "Usage:\n"
        "    python fetch.py videos CHANNEL_URL\n"
        "    python fetch.py metadata CHANNEL_URL"
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


if __name__ == "__main__":
    main(sys.argv[1:])

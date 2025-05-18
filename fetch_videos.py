#!/usr/bin/env python3
"""Fetch list of YouTube videos from a channel URL.

Usage:
    python fetch_videos.py https://www.youtube.com/@sequoiacapital/videos

Requires the ``yt-dlp`` package. Install via ``pip install yt-dlp``.
"""

from __future__ import annotations

import re
import sys
from typing import List

from yt_dlp import YoutubeDL


def _normalize_channel_url(url: str) -> str:
    """Strip trailing segments like ``/videos`` and return channel root URL."""
    m = re.match(r"(https?://www\.youtube\.com/[^/]+)", url)
    if not m:
        raise ValueError(f"Unrecognized YouTube URL: {url}")
    return m.group(1)


def fetch_video_urls(channel_url: str) -> List[str]:
    """Return list of video URLs for the channel using ``yt-dlp``."""
    ydl_opts = {
        "extract_flat": True,
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


def main(args: List[str]) -> None:
    if len(args) != 1:
        print("Usage: python fetch_videos.py CHANNEL_URL")
        raise SystemExit(1)
    channel_root = _normalize_channel_url(args[0])
    for video_url in fetch_video_urls(channel_root):
        print(video_url)


if __name__ == "__main__":
    main(sys.argv[1:])

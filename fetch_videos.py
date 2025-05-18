#!/usr/bin/env python3
"""Fetch list of YouTube videos from a channel URL.

Usage:
    python fetch_videos.py https://www.youtube.com/@sequoiacapital/videos

Requires the ``pytube`` package. Install via ``pip install pytube``.
"""

from __future__ import annotations

import re
import sys
from typing import List

from pytube import Channel


def _normalize_channel_url(url: str) -> str:
    """Strip trailing segments like ``/videos`` and return channel root URL."""
    m = re.match(r"(https?://www\.youtube\.com/[^/]+)", url)
    if not m:
        raise ValueError(f"Unrecognized YouTube URL: {url}")
    return m.group(1)


def fetch_video_urls(channel_url: str) -> List[str]:
    """Return list of video URLs for the channel."""
    channel = Channel(channel_url)
    return list(channel.video_urls)


def main(args: List[str]) -> None:
    if len(args) != 1:
        print("Usage: python fetch_videos.py CHANNEL_URL")
        raise SystemExit(1)
    channel_root = _normalize_channel_url(args[0])
    for video_url in fetch_video_urls(channel_root):
        print(video_url)


if __name__ == "__main__":
    main(sys.argv[1:])

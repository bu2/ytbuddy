#!/usr/bin/env python3
"""Fetch metadata for all videos in a YouTube channel.

Usage:
    python fetch_metadata.py CHANNEL_URL
"""

from __future__ import annotations

import json
import sys
from typing import Any, Dict, List

from yt_dlp import YoutubeDL

from fetch_videos import _normalize_channel_url, fetch_video_urls


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
    video_urls = fetch_video_urls(channel_root)
    metadata = []
    for url in video_urls:
        metadata.append(fetch_video_metadata(url))
    return metadata


def main(args: List[str]) -> None:
    if len(args) != 1:
        print("Usage: python fetch_metadata.py CHANNEL_URL")
        raise SystemExit(1)
    all_metadata = fetch_all_metadata(args[0])
    print(json.dumps(all_metadata, indent=2))


if __name__ == "__main__":
    main(sys.argv[1:])

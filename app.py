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
from datetime import datetime, date
from typing import Any, Dict, List

from youtube_transcript_api import YouTubeTranscriptApi

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


def _parse_upload_date(date_str: str | None) -> date | None:
    """Return a ``datetime.date`` parsed from ``YYYYMMDD`` format."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y%m%d").date()
    except (ValueError, TypeError):
        return None


def fetch_video_metadata(video_url: str) -> Dict[str, Any]:
    """Return metadata for a single YouTube video."""
    ydl_opts = {
        "skip_download": True,
        "quiet": True,
    }
    with YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(video_url, download=False)
    info["upload_date"] = _parse_upload_date(info.get("upload_date"))
    return info


def fetch_transcript(video_url: str) -> List[Dict[str, str]]:
    """Return the transcript for a YouTube video."""
    m = re.search(r"v=([^&]+)", video_url)
    if not m:
        m = re.search(r"youtu\.be/([^?&]+)", video_url)
    if not m:
        raise ValueError(f"Could not parse video ID from URL: {video_url}")
    video_id = m.group(1)
    return YouTubeTranscriptApi.get_transcript(video_id)


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

    metadata.sort(
        key=lambda m: m.get("upload_date") or date.min,
        reverse=True,
    )
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
        print(json.dumps(all_metadata, indent=2, default=str))
        with open("metadata.json", "w", encoding="utf-8") as fp:
            json.dump(all_metadata, fp, indent=2, default=str)


THUMBNAIL_TEMPLATE = '''
**{title}**

Published: {upload_date}

Views: {view_count}

Duration: {duration_string}
'''


def _render_metadata(
    st,
    metadata: List[Dict[str, Any]],
    container,
    selected: set,
) -> None:
    """Display video metadata thumbnails with selection checkboxes."""
    num_cols = 5
    columns = []
    for i, info in enumerate(metadata, start=1):
        if (i - 1) % num_cols == 0:
            columns = container.columns(num_cols)
        col = columns[(i - 1) % num_cols]
        thumb_url = info.get("thumbnail") or next(
            (t["url"] for t in info.get("thumbnails", []) if "url" in t),
            None,
        )
        if thumb_url:
            col.image(thumb_url, use_container_width=True)
        col.markdown(
            THUMBNAIL_TEMPLATE.format(
                **{
                    "title": info.get("title", "Untitled"),
                    "upload_date": info.get("upload_date"),
                    "view_count": info.get("view_count"),
                    "duration_string": info.get("duration_string"),
                }
            )
        )
        key = f"video_{i}"
        is_checked = st.session_state.get(key, False)
        disabled = len(selected) >= 10 and not is_checked
        checked = col.checkbox("Select", key=key, disabled=disabled)
        if checked:
            selected.add(info.get("webpage_url"))
        else:
            selected.discard(info.get("webpage_url"))
    st.session_state["selected_videos"] = selected


def run_streamlit() -> None:
    """Launch the Streamlit UI."""
    import streamlit as st

    st.set_page_config(page_title="YouTube Metadata Fetcher", layout="wide")

    st.title("YouTube Metadata Fetcher")

    if "selected_videos" not in st.session_state:
        st.session_state["selected_videos"] = set()
    if "metadata" not in st.session_state:
        st.session_state["metadata"] = []
    if "video_urls" not in st.session_state:
        st.session_state["video_urls"] = []
    if "transcripts" not in st.session_state:
        st.session_state["transcripts"] = {}

    channel_url = st.text_input("YouTube Channel URL")
    results_container = st.container()

    if st.button("Fetch Metadata") and channel_url:
        st.write("Fetching video list...")
        video_urls = fetch_video_urls(channel_url)
        st.session_state["video_urls"] = video_urls
        st.session_state["metadata"] = []
        st.session_state["selected_videos"] = set()
        st.write(f"Found {len(video_urls)} videos.")

        progress_bar = st.progress(0)
        status = st.empty()
        metadata: List[Dict[str, Any]] = []

        for i, info in enumerate(fetch_metadata_stream(channel_url), start=1):
            metadata.append(info)
            progress_bar.progress(i / len(video_urls))
            status.write(f"Fetched {i}/{len(video_urls)}: {info.get('title')}")

        progress_bar.empty()
        status.empty()

        metadata.sort(
            key=lambda m: m.get("upload_date") or date.min,
            reverse=True,
        )
        with open("metadata.json", "w", encoding="utf-8") as fp:
            json.dump(metadata, fp, indent=2, default=str)
        st.session_state["metadata"] = metadata
        st.success("Done fetching metadata")
        st.caption("Select up to 10 videos.")
        selected = st.session_state["selected_videos"]
        _render_metadata(st, metadata, results_container, selected)
        st.write(f"Selected {len(selected)}/10 videos")
    elif st.session_state["metadata"]:
        st.caption("Select up to 10 videos.")
        metadata = st.session_state["metadata"]
        selected = st.session_state["selected_videos"]
        _render_metadata(st, metadata, results_container, selected)
        st.write(f"Selected {len(selected)}/10 videos")

    if st.session_state.get("selected_videos"):
        if st.button("Fetch Transcripts"):
            selected_urls = list(st.session_state["selected_videos"])
            progress_bar = st.progress(0)
            transcripts: Dict[str, List[Dict[str, str]]] = {}
            for i, url in enumerate(selected_urls, start=1):
                try:
                    transcripts[url] = fetch_transcript(url)
                except Exception as exc:  # noqa: BLE001
                    transcripts[url] = [{"error": str(exc)}]
                progress_bar.progress(i / len(selected_urls))
            progress_bar.empty()
            st.session_state["transcripts"] = transcripts
            with open("transcripts.json", "w", encoding="utf-8") as fp:
                json.dump(transcripts, fp, indent=2, ensure_ascii=False)
            st.success("Done fetching transcripts")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1:])
    else:
        run_streamlit()

"""
wiz_yt.py — Sync your WiZ bulbs to YouTube playing on your TV. No camera.

Talks to your TV's YouTube app directly over your WiFi using YouTube's "Lounge"
API — the same mechanism that lets your phone act as a remote ("Play on TV").
Once paired, the TV pushes live now-playing events (video id, play/pause). We
take the video's thumbnail, pull its dominant colors, and stream them to your
bulbs over your LAN.

One-time pairing:
  On the TV, open YouTube > Settings > "Link with TV code" — it shows a code.
  Enter that code when this script asks. It's saved, so you only do it once.

Run:  python wiz_yt.py
Stop: Ctrl-C
"""

from __future__ import annotations

import asyncio
import json
import os
import sys

import aiohttp
from pyytlounge import EventListener, YtLoungeApi

from wiz_bulbs import apply_colors, get_bulbs
from wiz_music import palette_from_artwork  # reuse the album-art color extractor

DEVICE_NAME = "wiz-music"
AUTH_FILE = os.path.join(os.path.dirname(__file__), ".yt_auth.json")


# ---------------------------------------------------------------------------
# Thumbnail fetching
# ---------------------------------------------------------------------------

async def fetch_thumbnail(session: aiohttp.ClientSession, video_id: str) -> bytes | None:
    """Grab the best available thumbnail for a video (maxres → hq fallback)."""
    for name in ("maxresdefault", "sddefault", "hqdefault"):
        url = f"https://img.youtube.com/vi/{video_id}/{name}.jpg"
        try:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
                if r.status == 200:
                    data = await r.read()
                    if len(data) > 1500:  # missing thumbs return a tiny placeholder
                        return data
        except Exception:
            pass
    return None


# ---------------------------------------------------------------------------
# Event listener — fires whenever the TV changes what's playing
# ---------------------------------------------------------------------------

class ColorListener(EventListener):
    def __init__(self, bulbs, session):
        self.bulbs = bulbs
        self.session = session
        self.last_video = None

    async def now_playing_changed(self, event) -> None:
        vid = event.video_id
        if not vid or vid == self.last_video:
            return
        self.last_video = vid

        data = await fetch_thumbnail(self.session, vid)
        if not data:
            print(f"▶ {vid}  (no thumbnail)")
            return

        colors = palette_from_artwork(data, len(self.bulbs))
        swatch = "  ".join(f"\x1b[48;2;{r};{g};{b}m   \x1b[0m" for r, g, b in colors)
        print(f"▶ {vid}  {swatch}  {colors}")
        await apply_colors(self.bulbs, colors)

    async def disconnected(self, event) -> None:
        print("\nDisconnected from the TV.")


# ---------------------------------------------------------------------------
# Pairing + connect
# ---------------------------------------------------------------------------

async def ensure_paired(api: YtLoungeApi) -> None:
    if os.path.exists(AUTH_FILE):
        try:
            with open(AUTH_FILE) as f:
                api.load_auth_state(json.load(f))
        except Exception:
            print("Saved pairing couldn't be read — let's pair again.")

    if api.paired():
        return

    print(
        "\nOne-time pairing:\n"
        "  On your TV, open YouTube > Settings > 'Link with TV code'.\n"
        "  It shows a code like '123 456 789 012'.\n"
    )
    code = input("Enter the TV code: ").strip().replace(" ", "")
    if not await api.pair(code):
        sys.exit("Pairing failed. Double-check the code and try again.")
    # Note: use auth.serialize() (not store_auth_state()) — it's the format
    # load_auth_state() expects; the two are mismatched in pyytlounge.
    with open(AUTH_FILE, "w") as f:
        json.dump(api.auth.serialize(), f)
    print("Paired and saved — you won't need the code next time.\n")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    bulbs = await get_bulbs()

    async with aiohttp.ClientSession() as session:
        listener = ColorListener(bulbs, session)
        # YtLoungeApi must be used as an async context manager so it can set up
        # its own HTTP session.
        async with YtLoungeApi(DEVICE_NAME, event_listener=listener) as api:
            await ensure_paired(api)

            if not await api.connect():
                sys.exit(
                    "Couldn't connect to the TV. Make sure the TV is on with "
                    "YouTube open, then rerun. If it keeps failing, delete "
                    ".yt_auth.json to re-pair."
                )

            print("Connected. Play something on the TV's YouTube. Ctrl-C to stop.\n")
            await api.get_now_playing()   # color the current video immediately
            await api.subscribe()          # blocks, feeding events to the listener


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")

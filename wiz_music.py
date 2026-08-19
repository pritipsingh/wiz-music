"""
wiz_music.py — Make your WiZ bulbs take on the color of whatever's playing.

Reads the macOS system "Now Playing" info (works for BOTH the Spotify app and
YouTube in a browser — anything that shows up in Control Center), grabs the
current track's album artwork, extracts its dominant colors, and pushes them to
your WiZ bulbs over your local network. No API keys, no Spotify developer app.

Note: this reads *this Mac's* playback. For music on a phone or TV, see the
other modes in the README.

Run:  python wiz_music.py
Stop: Ctrl-C
"""

from __future__ import annotations

import asyncio
import base64
import io
import subprocess
import sys

from colorthief import ColorThief

from wiz_bulbs import apply_colors, get_bulbs, punch

POLL_SECONDS = 2.0          # how often to check what's playing


# ---------------------------------------------------------------------------
# macOS "Now Playing" — the universal source (Spotify app + YouTube in browser)
# ---------------------------------------------------------------------------

def _nowplaying(*props: str) -> list[str]:
    """Call nowplaying-cli and return the requested properties, one per line."""
    try:
        out = subprocess.run(
            ["nowplaying-cli", "get", *props],
            capture_output=True, text=True, timeout=5,
        )
    except FileNotFoundError:
        sys.exit(
            "nowplaying-cli not found.\n"
            "Install it with:  brew install nowplaying-cli"
        )
    return out.stdout.splitlines()


def current_track() -> tuple[str, bytes | None]:
    """Return (track_id, artwork_bytes) for whatever is currently playing."""
    title_artist = _nowplaying("title", "artist")
    title = title_artist[0] if len(title_artist) > 0 else ""
    artist = title_artist[1] if len(title_artist) > 1 else ""
    track_id = f"{artist} — {title}".strip(" —")

    art_lines = _nowplaying("artworkData")
    art_b64 = art_lines[0] if art_lines else ""
    artwork = None
    if art_b64 and art_b64 != "null":
        try:
            artwork = base64.b64decode(art_b64)
        except Exception:
            artwork = None
    return track_id, artwork


def palette_from_artwork(artwork: bytes, count: int) -> list[tuple[int, int, int]]:
    """Pull a small palette of punchy colors from the album art."""
    thief = ColorThief(io.BytesIO(artwork))
    try:
        raw = thief.get_palette(color_count=max(count + 1, 3), quality=5)
    except Exception:
        raw = [thief.get_color(quality=5)]
    colors = [punch(c) for c in raw]
    # Repeat to cover all bulbs if the palette is short.
    while len(colors) < count:
        colors += colors
    return colors[:count]


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

async def main():
    bulbs = await get_bulbs()
    print("Watching what's playing. Press Ctrl-C to stop.\n")
    last_track = None
    while True:
        track_id, artwork = current_track()
        if track_id and track_id != last_track and artwork:
            colors = palette_from_artwork(artwork, len(bulbs))
            swatch = "  ".join(f"\x1b[48;2;{r};{g};{b}m   \x1b[0m" for r, g, b in colors)
            print(f"♪ {track_id}\n  {swatch}  {colors}")
            await apply_colors(bulbs, colors)
            last_track = track_id
        await asyncio.sleep(POLL_SECONDS)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")

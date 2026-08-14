"""
wiz_music.py — Make your WiZ bulbs take on the color of whatever's playing.

Reads the macOS system "Now Playing" info (works for BOTH the Spotify app and
YouTube in a browser — anything that shows up in Control Center), grabs the
current track's album artwork, extracts its dominant colors, and pushes them to
your WiZ bulbs over your local network. No API keys, no Spotify developer app.

Run:  python wiz_music.py
Stop: Ctrl-C
"""

from __future__ import annotations

import asyncio
import base64
import colorsys
import io
import socket
import subprocess
import sys

from colorthief import ColorThief
from pywizlight import PilotBuilder, wizlight
from pywizlight.discovery import discover_lights

# ---------------------------------------------------------------------------
# Config — tweak these
# ---------------------------------------------------------------------------

# Leave empty to auto-discover bulbs on your network, OR hardcode the IPs, e.g.
#   BULB_IPS = ["192.168.1.42", "192.168.1.43"]
BULB_IPS: list[str] = []

POLL_SECONDS = 2.0          # how often to check what's playing
SATURATION_BOOST = 1.5      # album colors are often muddy; punch them up
MIN_BRIGHTNESS = 140        # 0-255, so a dark cover doesn't go near-black
MAX_BRIGHTNESS = 255


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


# ---------------------------------------------------------------------------
# Color extraction
# ---------------------------------------------------------------------------

def _punch(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    """Boost saturation and floor the brightness so it looks good on a bulb."""
    r, g, b = (c / 255 for c in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    s = min(1.0, s * SATURATION_BOOST)
    v = max(v, 0.55)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


def palette_from_artwork(artwork: bytes, count: int) -> list[tuple[int, int, int]]:
    """Pull a small palette of punchy colors from the album art."""
    thief = ColorThief(io.BytesIO(artwork))
    try:
        raw = thief.get_palette(color_count=max(count + 1, 3), quality=5)
    except Exception:
        raw = [thief.get_color(quality=5)]
    colors = [_punch(c) for c in raw]
    # Repeat to cover all bulbs if the palette is short.
    while len(colors) < count:
        colors += colors
    return colors[:count]


# ---------------------------------------------------------------------------
# Bulb discovery + control
# ---------------------------------------------------------------------------

def _broadcast_address() -> str:
    """Best-effort local /24 broadcast address, e.g. 192.168.1.255."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip.rsplit(".", 1)[0] + ".255"


async def get_bulbs() -> list[wizlight]:
    if BULB_IPS:
        return [wizlight(ip) for ip in BULB_IPS]
    bcast = _broadcast_address()
    print(f"Discovering WiZ bulbs on {bcast} ...")
    bulbs = await discover_lights(broadcast_space=bcast)
    if not bulbs:
        sys.exit(
            "No bulbs found. Make sure they're on the same WiFi, or set "
            "BULB_IPS at the top of this file."
        )
    print(f"Found {len(bulbs)} bulb(s): {', '.join(b.ip for b in bulbs)}")
    return bulbs


async def apply_colors(bulbs, colors):
    async def one(bulb, rgb):
        try:
            await bulb.turn_on(PilotBuilder(rgb=rgb, brightness=MAX_BRIGHTNESS))
        except Exception as e:
            print(f"  ! {bulb.ip}: {e}")
    await asyncio.gather(*(one(b, colors[i]) for i, b in enumerate(bulbs)))


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

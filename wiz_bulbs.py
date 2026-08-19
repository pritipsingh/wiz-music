"""
wiz_bulbs.py — Shared WiZ bulb discovery, control, and color helpers.

Used by both wiz_music.py (album-art mode) and wiz_ambient.py (webcam mode).
WiZ bulbs are controlled locally with JSON "setPilot" messages sent as UDP
datagrams on port 38899 — pywizlight handles that wire format for us.
"""

from __future__ import annotations

import asyncio
import colorsys
import socket
import sys

from pywizlight import PilotBuilder, wizlight
from pywizlight.discovery import discover_lights

# ---------------------------------------------------------------------------
# Config — shared by both modes
# ---------------------------------------------------------------------------

# Leave empty to auto-discover bulbs on your network, OR hardcode the IPs, e.g.
#   BULB_IPS = ["192.168.1.18", "192.168.1.14"]
BULB_IPS: list[str] = []

SATURATION_BOOST = 1.5      # colors are often muddy; punch them up
MIN_VALUE = 0.55            # HSV value floor so dark scenes don't go black
BRIGHTNESS = 255            # 0-255 bulb brightness


# ---------------------------------------------------------------------------
# Color helper
# ---------------------------------------------------------------------------

def punch(rgb: tuple[int, int, int]) -> tuple[int, int, int]:
    """Boost saturation and floor the brightness so it looks good on a bulb."""
    r, g, b = (c / 255 for c in rgb)
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    s = min(1.0, s * SATURATION_BOOST)
    v = max(v, MIN_VALUE)
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return (int(r * 255), int(g * 255), int(b * 255))


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
    """Return the configured bulbs, or auto-discover them on the LAN."""
    if BULB_IPS:
        return [wizlight(ip) for ip in BULB_IPS]
    bcast = _broadcast_address()
    print(f"Discovering WiZ bulbs on {bcast} ...")
    bulbs = await discover_lights(broadcast_space=bcast)
    if not bulbs:
        sys.exit(
            "No bulbs found. Make sure they're on the same WiFi, or set "
            "BULB_IPS at the top of wiz_bulbs.py."
        )
    print(f"Found {len(bulbs)} bulb(s): {', '.join(b.ip for b in bulbs)}")
    return bulbs


async def apply_colors(bulbs, colors) -> None:
    """Send one color per bulb (cycling the list if it's shorter than bulbs)."""
    async def one(bulb, rgb):
        try:
            await bulb.turn_on(PilotBuilder(rgb=rgb, brightness=BRIGHTNESS))
        except Exception as e:
            print(f"  ! {bulb.ip}: {e}")
    await asyncio.gather(
        *(one(b, colors[i % len(colors)]) for i, b in enumerate(bulbs))
    )

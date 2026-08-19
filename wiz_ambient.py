"""
wiz_ambient.py — Ambilight-style sync: your bulbs follow whatever's on screen.

Point a webcam at your TV (or any screen) and this reads the dominant color of
the picture in real time and streams it to your WiZ bulbs over your LAN. Because
it watches the *screen*, it works with anything — YouTube on a smart TV,
Netflix, games — with no metadata or API needed.

Point the camera so the TV fills as much of the frame as possible.

Run:  python wiz_ambient.py
Stop: Ctrl-C
"""

from __future__ import annotations

import asyncio
import sys

try:
    import cv2
    import numpy as np
except ImportError:
    sys.exit(
        "This mode needs OpenCV. Install it with:\n"
        "    pip install opencv-python"
    )

from wiz_bulbs import apply_colors, get_bulbs, punch

# ---------------------------------------------------------------------------
# Config — tweak these
# ---------------------------------------------------------------------------

CAMERA_INDEX = 0        # 0 = default camera; try 1, 2... for a USB webcam
CROP = 1.0              # 1.0 = whole frame; lower (e.g. 0.7) to zoom into the TV
SMOOTHING = 0.25        # 0-1: lower = smoother/dreamier, higher = snappier
SEND_INTERVAL = 0.2     # seconds between bulb updates (don't spam the bulbs)
FRAME_INTERVAL = 0.03   # seconds between camera reads (~30 fps)


# ---------------------------------------------------------------------------
# Dominant color of a video frame
# ---------------------------------------------------------------------------

def _crop_center(frame, frac: float):
    if frac >= 0.999:
        return frame
    h, w = frame.shape[:2]
    cw, ch = int(w * frac), int(h * frac)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    return frame[y0:y0 + ch, x0:x0 + cw]


def _saturation_bgr(c) -> float:
    b, g, r = float(c[0]), float(c[1]), float(c[2])
    mx, mn = max(r, g, b), min(r, g, b)
    return 0.0 if mx == 0 else (mx - mn) / mx


def dominant_color(frame) -> tuple[int, int, int]:
    """
    Find the dominant color of a frame with k-means clustering, biased toward
    colorful clusters so dark bars / backgrounds don't win over the real color.
    """
    small = cv2.resize(frame, (80, 45), interpolation=cv2.INTER_AREA)
    data = small.reshape(-1, 3).astype(np.float32)  # OpenCV frames are BGR
    k = 4
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(
        data, k, None, criteria, 3, cv2.KMEANS_PP_CENTERS
    )
    counts = np.bincount(labels.flatten(), minlength=k).astype(np.float32)
    sats = np.array([_saturation_bgr(c) for c in centers])
    scores = counts * (0.15 + sats)     # populous AND colorful wins
    b, g, r = centers[int(np.argmax(scores))]
    return (int(r), int(g), int(b))


def _lerp(a, b, t: float):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


# ---------------------------------------------------------------------------
# Main loop
# ---------------------------------------------------------------------------

async def main():
    bulbs = await get_bulbs()

    cap = cv2.VideoCapture(CAMERA_INDEX)
    if not cap.isOpened():
        sys.exit(
            f"Couldn't open the webcam (index {CAMERA_INDEX}).\n"
            "- Check System Settings > Privacy & Security > Camera and allow "
            "your terminal.\n"
            "- Try a different CAMERA_INDEX (1, 2, ...) for a USB webcam."
        )

    print("Ambient sync running. Point the camera at the TV. Ctrl-C to stop.\n")
    loop = asyncio.get_event_loop()
    smoothed = None
    last_send = last_print = 0.0
    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                await asyncio.sleep(0.1)
                continue

            target = punch(dominant_color(_crop_center(frame, CROP)))
            smoothed = target if smoothed is None else _lerp(smoothed, target, SMOOTHING)

            now = loop.time()
            if now - last_send >= SEND_INTERVAL:
                await apply_colors(bulbs, [smoothed])
                last_send = now
                if now - last_print >= 1.0:
                    r, g, b = smoothed
                    print(
                        f"\r\x1b[48;2;{r};{g};{b}m     \x1b[0m rgb{smoothed}    ",
                        end="", flush=True,
                    )
                    last_print = now
            await asyncio.sleep(FRAME_INTERVAL)
    finally:
        cap.release()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nStopped.")

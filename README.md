# 🎵💡 wiz-music

**Make your WiZ smart bulbs take on the color of whatever you're playing.**

Two ways to light your room to your music, both streaming colors to your bulbs
locally over your WiFi — no cloud services, no lag:

| Mode | Script | What it follows | Best for |
|---|---|---|---|
| 🎨 **Album art** | `wiz_music.py` | The cover art of the track playing on your Mac | Spotify / YouTube on your Mac |
| 📺 **YouTube on TV** | `wiz_yt.py` | The video playing on your TV's YouTube app | YouTube on a **smart TV**, no camera |
| 🎥 **Ambient (Ambilight)** | `wiz_ambient.py` | The live colors on a screen, via a webcam | Netflix/games on a TV, any screen |

> Album art → dominant colors → your room. Or a screen → your room. The song is
> *there*, in the light.

---

## Mode 1 — Album art (`wiz_music.py`)

Play a song on your Mac and the lights melt into the colors of the album cover.

```
 ┌─────────────┐    now playing    ┌──────────────┐   dominant     ┌──────────┐
 │  Spotify /  │ ────────────────▶ │  wiz_music   │   colors 🎨    │   WiZ    │
 │  YouTube    │   title + cover   │  (your Mac)  │ ─────────────▶ │  bulbs   │
 └─────────────┘                   └──────────────┘   UDP / LAN     └──────────┘
```

1. **Read what's playing.** macOS keeps a system-wide "Now Playing" record (the
   thing in Control Center) with metadata *and album artwork* from both the
   **Spotify app** and **YouTube in a browser** — one source covers both.
2. **Extract the palette.** The cover art is run through a dominant-color
   extractor ([Modified Median Cut Quantization](https://en.wikipedia.org/wiki/Median_cut)),
   then saturation-boosted so it pops on a bulb instead of looking muddy.
3. **Push to the bulbs — locally.** WiZ bulbs take JSON `setPilot` commands as
   UDP packets on port `38899`. Script and bulbs share the **same LAN**, so it's
   instant — no internet round-trip, no account.

> ⚠️ This reads *this Mac's* playback. Music on a phone or TV won't be seen — for
> a TV, use Mode 2.

## Mode 2 — YouTube on a TV (`wiz_yt.py`)

Play YouTube on your smart TV and the bulbs follow the video — **no camera**.
It talks to the TV's YouTube app directly over your WiFi using YouTube's
"Lounge" API (the same thing that lets your phone be a remote — "Play on TV").

```
┌──────────┐  now playing   ┌──────────────┐  video thumb   ┌──────────┐
│ TV's YT   │ ────────────▶ │   wiz_yt      │  → colors 🎨   │   WiZ    │
│   app     │  (Lounge API)  │  (your Mac)   │ ────────────▶ │  bulbs   │
└──────────┘                 └──────────────┘   UDP / LAN     └──────────┘
```

1. **Pair once.** On the TV: YouTube → Settings → *Link with TV code*. Enter the
   code when the script asks. It's saved (`.yt_auth.json`), so you never re-pair.
2. **Get live now-playing.** The TV pushes events — the current **video id** and
   play/pause — straight to your Mac.
3. **Color from the thumbnail.** The video's thumbnail is fetched, run through
   the same dominant-color extractor as Mode 1, and streamed to the bulbs.

```bash
python wiz_yt.py
```

> Colors come from the video **thumbnail** (one identity color per video), not
> per-scene — for that, use Mode 3. But it needs no camera and no cloud.

## Mode 3 — Ambient / Ambilight (`wiz_ambient.py`)

Point a **webcam at your TV** and the bulbs follow the colors on screen in real
time. Since it watches the *picture*, it works with anything — YouTube on a
smart TV, Netflix, games — with no metadata or API.

```
┌──────────┐   points at    ┌─────────────┐  dominant     ┌──────────┐
│   TV      │ ◀──────────── │  webcam +    │  color 🎨     │   WiZ    │
│ (YouTube) │                │  your Mac    │ ────────────▶ │  bulbs   │
└──────────┘                └─────────────┘   UDP / LAN     └──────────┘
```

The frame is clustered with k-means to find its dominant color (biased toward
colorful regions so black bars don't win), smoothed over time so the light
glides instead of strobing, then sent to the bulbs — reusing the exact same
local WiZ control code as Mode 1.

> Point the camera so the TV fills as much of the frame as possible. For the
> cleanest result, an HDMI-capture setup beats a webcam — but that only works if
> an external stick (Chromecast/Apple TV) feeds the TV, not the TV's own app.

---

## Setup

**Requirements:** macOS (≤ 14.x recommended), Python 3.9+, WiZ bulbs on the same
WiFi as your Mac. Mode 2 also needs a webcam.

```bash
# The macOS "now playing" reader (Mode 1 only)
brew install nowplaying-cli

# Python deps (in a virtualenv)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
source .venv/bin/activate

python wiz_music.py      # Mode 1: album art from Mac playback
python wiz_yt.py         # Mode 2: YouTube on a TV (no camera)
python wiz_ambient.py    # Mode 3: ambient color from a webcam
```

### macOS menu bar controller

Build a small native app for manual color, brightness, and power control:

```bash
./build_menubar_app.sh
open "dist/WiZ Light.app"
```

The app starts with the last discovered bulb address. Change the address in
the popover if your router assigns the bulb a new IP.

Both auto-discover your bulbs on the LAN and print live color swatches as they
run. `Ctrl-C` to stop.

```
Found 2 bulb(s): 192.168.1.18, 192.168.1.14
♪ Rahat Fateh Ali Khan — Laal Ishq
  ██  ██   [(196, 38, 42), (28, 20, 34)]
```

---

## Tuning

Shared bulb + color settings live in [`wiz_bulbs.py`](wiz_bulbs.py):

| Setting | What it does |
|---|---|
| `BULB_IPS` | Leave empty to auto-discover, or hardcode IPs for reliability. |
| `SATURATION_BOOST` | Higher = more vivid (colors are often muddy). |
| `MIN_VALUE` | Brightness floor so dark scenes don't go black. |
| `BRIGHTNESS` | Bulb brightness, 0-255. |

Ambient mode adds its own knobs at the top of [`wiz_ambient.py`](wiz_ambient.py):
`CAMERA_INDEX`, `CROP` (zoom into the TV), `SMOOTHING` (dreamy ↔ snappy),
`SEND_INTERVAL`.

**Bulbs not found?** Auto-discovery can be flaky on some routers. Open the WiZ
app → each bulb's settings shows its IP → paste them into `BULB_IPS`.

---

## The WiZ protocol (nerdy bit)

No cloud, no pairing handshake. WiZ bulbs listen for **JSON over UDP** on port
`38899`. Setting a color is a single packet:

```json
{"method": "setPilot", "params": {"r": 196, "g": 38, "b": 42, "dimming": 100}}
```

The bulb applies it instantly and replies `{"result": {"success": true}}`.
Discovery is the same packet broadcast to the whole subnet. `pywizlight` builds
these for us so the code just calls `.turn_on(rgb=...)`.

---

## Notes & limitations

- **Mode 1** needs playback on *this* Mac; **macOS 15.4+** locked down the Now
  Playing API for third-party tools, so it works best on 14.x and earlier.
- **Mode 2** (webcam) is affected by room lighting and camera angle — aim it so
  the TV fills the frame, and dim other lights for the cleanest read.

## Roadmap ideas

- [x] **YouTube-on-TV mode** — read now-playing from the TV via the Lounge API.
- [x] **Ambient / Ambilight mode** — sync to any screen via a webcam.
- [ ] **Spotify Web API mode** — read playback from the cloud so any device
      (phone, TV's Spotify app) works, not just this Mac.
- [ ] **Scene-reactive YouTube** — sample the video timeline instead of one
      thumbnail, so colors shift through the video without a camera.
- [ ] **Audio-reactive mode** — capture system audio and pulse to the beat.
- [ ] Run headless on a Raspberry Pi for an always-on setup.

---

## Built with

- [`pywizlight`](https://github.com/sbidy/pywizlight) — local control of WiZ bulbs
- [`nowplaying-cli`](https://github.com/kirtan-shah/nowplaying-cli) — macOS Now Playing reader
- [`colorthief`](https://github.com/fengsp/color-thief-py) — album-art color extraction
- [`pyytlounge`](https://github.com/FabioGNR/pyytlounge) — YouTube Lounge API (TV now-playing)
- [`opencv-python`](https://github.com/opencv/opencv-python) — webcam capture + frame color clustering

## License

MIT — do whatever you want with it.

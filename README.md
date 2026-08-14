# 🎵💡 wiz-music

**Make your WiZ smart bulbs take on the color of whatever music you're playing.**

Play a song on Spotify or YouTube, and your lights melt into the colors of the
album art — in real time. No cloud services, no lag: your Mac reads what's
playing, pulls the dominant colors from the cover art, and beams them straight
to your bulbs over your local WiFi.

> Album art → dominant colors → your room. The song is *there*, in the light.

---

## How it works

```
 ┌─────────────┐    now playing    ┌──────────────┐   dominant     ┌──────────┐
 │  Spotify /  │ ────────────────▶ │  wiz_music   │   colors 🎨    │   WiZ    │
 │  YouTube    │   title + cover   │  (your Mac)  │ ─────────────▶ │  bulbs   │
 └─────────────┘                   └──────────────┘   UDP / LAN     └──────────┘
```

1. **Read what's playing.** macOS keeps a system-wide "Now Playing" record (the
   thing in Control Center). It captures metadata *and album artwork* from both
   the **Spotify app** and **YouTube in a browser** — so one source covers both.
2. **Extract the palette.** The cover art is run through a dominant-color
   extractor, and the colors are saturation-boosted so they actually pop on a
   bulb instead of looking muddy.
3. **Push to the bulbs — locally.** WiZ bulbs are controlled with small UDP
   packets over your own network (port `38899`). The script and the bulbs sit on
   the **same LAN**, so it's instant — no internet round-trip, no cloud account.

Multiple bulbs each get a different color from the cover's palette, and the
lights only change when the track changes — calm, not flickery.

---

## Setup

**Requirements:** macOS (≤ 14.x recommended), Python 3.9+, and WiZ bulbs on the
same WiFi as your Mac.

```bash
# 1. The macOS "now playing" reader
brew install nowplaying-cli

# 2. Python deps (in a virtualenv)
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
source .venv/bin/activate
python wiz_music.py
```

Hit play on Spotify or YouTube. When the track changes, the bulbs update to
match the cover art. `Ctrl-C` to stop.

```
Found 2 bulb(s): 192.168.1.18, 192.168.1.14
Watching what's playing. Press Ctrl-C to stop.

♪ Rahat Fateh Ali Khan — Laal Ishq
  ██  ██   [(196, 38, 42), (28, 20, 34)]
```

---

## Tuning

All the knobs live at the top of [`wiz_music.py`](wiz_music.py):

| Setting | What it does |
|---|---|
| `BULB_IPS` | Leave empty to auto-discover, or hardcode IPs for reliability. |
| `SATURATION_BOOST` | Higher = more vivid (album colors are often muddy). |
| `MIN_BRIGHTNESS` / `MAX_BRIGHTNESS` | Keep dark covers from going near-black. |
| `POLL_SECONDS` | How often to check what's playing. |

**Bulbs not found?** Auto-discovery can be flaky on some routers. Open the WiZ
app → each bulb's settings shows its IP → paste them into `BULB_IPS`.

---

## Notes & limitations

- **Playback has to be on this Mac.** The script reads *this* machine's Now
  Playing, so playing on your phone won't be seen. (A Spotify Web API version
  that works from any device is on the roadmap below.)
- **macOS 15.4+** locked down the Now Playing API for third-party tools. If you
  upgrade and it stops seeing tracks, that's why.
- This matches the **cover-art color** (static per track). Beat-reactive pulsing
  is a separate audio-capture mode.

## Roadmap ideas

- [ ] **Spotify Web API mode** — read playback from the cloud so you can play on
      any device (phone included), not just this Mac.
- [ ] **Audio-reactive mode** — capture system audio and pulse the lights to the
      beat, for any source.
- [ ] Smooth color fades / transitions between tracks.
- [ ] Run headless on a Raspberry Pi for an always-on setup.

---

## Built with

- [`pywizlight`](https://github.com/sbidy/pywizlight) — local control of WiZ bulbs
- [`nowplaying-cli`](https://github.com/kirtan-shah/nowplaying-cli) — macOS Now Playing reader
- [`colorthief`](https://github.com/fengsp/color-thief-py) — dominant color extraction

## License

MIT — do whatever you want with it.

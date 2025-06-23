## Tesselate-AI v1 — “Digital Artisan” Spec

*(static-site edition, assets pre-baked by a Python CLI)*

### 1 · Target Player

* **Persona** Adults 30-60, casual puzzlers.
* **Skill ceiling** Up to ≈500 pieces; v1 ships one size: **256 pieces**.
* **Device** Desktop/laptop, Chrome/Firefox/Edge, mouse/track-pad.

### 2 · Gameplay & UI

| Feature           | Decision                                                                      |
| ----------------- | ----------------------------------------------------------------------------- |
| Piece orientation | Upright only (no rotation).                                                   |
| Scatter           | “Cardboard confetti” explosion on load.                                       |
| Board             | Fixed viewport, no zoom/pan.                                                  |
| Snap window       | ± **5 px** Manhattan distance to target.                                      |
| Grouping          | Pieces stay **individual**, even when locked.                                 |
| Ghost image       | Press-and-hold (default **Spacebar**) shows faint full image at 20 % opacity. |
| Timer             | Live clock + victory pop-up with solve time.                                  |
| Save state        | Local Storage checkpoint **optional** (feature-flag off by default).          |
| Telemetry         | One POST on completion (solve time + puzzle ID).                              |

### 3 · Front-End Stack

* **React 18 + Next.js 14** — built as a static export (`next export`).
* **Konva.js** canvas layer for drag, drop, hit-tests.
* Piece loader: lazy-fetch `piece_{id}.png` as the player grabs/zooms near them (simple `fetch` + cache).
* All assets served by the same Next.js static server; no CDN in v1.

### 4 · File & Data Layout

```
/public/puzzles/
   0001/
       manifest.json          // per-piece home coords (pixels)
       piece_000.png … piece_255.png  // 128×128 transparent squares
```

`manifest.json` schema:

```jsonc
{
  "size": 2048,                // full image width/height
  "grid": [16, 16],            // rows, cols
  "pieces": [
    { "id": 0, "x": 0,   "y": 0   },
    { "id": 1, "x": 128, "y": 0   },
    ...
  ]
}
```

No starting positions; the browser randomises scatter.

### 5 · Asset-Factory CLI (Python)

**One command** turns thin air into a ready-to-host puzzle set.

1. **Prompt Artisan**

   ```python
   prompt = ("Ultra-realistic wildlife photograph, varied textures, balanced composition, "
             "high detail, professional lighting, cinematic depth of field")
   ```

   * Hit **OpenAI images.generate**; seed with random wildlife subject each call (`random.choice(animal_list)`).

2. **Quality Guardian**

   * Loads JPEG → NumPy.
   * Metrics:

     * **Edge density** (OpenCV Canny edges / pixel count).
     * **Color entropy** (Shannon over 32-bin HSV histogram).
     * **Local contrast** (std-dev of Sobel magnitude).
   * Score = weighted sum, 0-100.
   * **Cut-off: 80**. Below that: re-prompt.

3. **Digital Cutter**

   * 16 × 16 grid, Bézier-perturbed jigsaw curves (classic squiggle).
   * For each cell:

     1. Generate SVG path.
     2. Mask original 2048² image → RGBA **128×128** PNG (transparent background).
   * Filenames `piece_{0-255}.png`.

4. **Bundler**

   * Writes `manifest.json`.
   * Repeats until **20** accepted puzzles exist.

### 6 · Sizing & Perf

* **Image res** 2048 × 2048 → \~8 MB source JPEG.
* 256 PNG pieces ≈ 15-18 MB total (with transparency).
* Worst-case first paint: 1 HTML + minimal JS (\~200 kB). Pieces lazy-load on demand.

### 7 · Extensibility Hooks

| Future v2 Idea         | Hook in v1                                                 |
| ---------------------- | ---------------------------------------------------------- |
| Variable piece counts  | Guardian/Cutter already parameterised by `rows, cols`.     |
| Tablet multitouch      | Konva supports pinch-zoom; board size stored in state.     |
| Account system         | Telemetry endpoint abstracted behind `/api/finish`.        |
| User-generated prompts | CLI logic extracted into micro-service callable over HTTP. |
| CDN move               | Asset URLs built from env var `ASSET_BASE_URL`.            |

### 8 · Open Questions (flagged for v2)

1. Piece-edge styling (drop shadows, bevel) for better grip?
2. Accessibility: high-contrast mode, keyboard drag?
3. Replay / best-time leaderboard.

---

**Done.** This spec nails down every moving part for a static-site launch: who plays, how it feels, where every byte lives, and the Python factory that forges it all. Hand it to any dev—or an AI coding copilot—and watch PuzzleForge spring to life.

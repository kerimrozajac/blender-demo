---
name: animation-render-validation
description: Diagnose image-sequence export, transparency, compositing, and video-encoding problems in Blender/Motion Canvas animation projects.
---

# Animation render validation

Use this skill when a render is incomplete, exports at the wrong size/rate, loses overlay alpha, composites out of sync, or produces a malformed final video.

## Establish the expected result

- Compute `frames = duration_seconds × fps` and require an integral frame count.
- Blender image sequences conventionally start at `frame0001.png`; Motion Canvas starts at `000000.png`; MP4 decoded frames start at index 0. Blender frame N must pair with overlay frame N−1.
- Both sources must have identical pixel dimensions and exactly the expected contiguous frame indices.
- PNG overlays must have an alpha channel. A design with persistent border/decoration can legitimately have nonzero alpha at the first and last frames.
- The final H.264 video should have the requested dimensions/FPS/frame count/duration and should contain an audio stream only when requested.

## Diagnose the stage that failed

1. Run `scripts/count_frames.sh <name> <frames>` and inspect whether filenames are contiguous. Do not encode short or extra sequences.
2. Check that the Motion Canvas UI says rendering is finished. Browser background throttling can make a render take much longer; keep the export page visible and poll its output directory until completion and stable count.
3. Confirm overlay PNGs are actually RGBA, not merely displayed over a checkerboard. `scripts/collect_overlay.py` rejects overlays without RGBA IHDR.
4. If one font resolves as a fallback, verify its `@fontsource` package is installed under `my-animation`, CSS import weight matches, `document.fonts.load(...)` completes before measurement, and Vite was restarted after dependency changes.
5. If the subject looks wrong, inspect the saved `.blend` and a representative render. Verify source orientation, camera axis, pivot placement, orthographic scale, and gradient UV frame before rerendering every frame.
6. Rebuild with validation enabled:

   ```sh
   python3 scripts/finalize_video.py <name> --fps <fps> --frames <frames>
   ```

   The tool checks sequence indexing, PNG dimensions, RGBA overlay channels, frame alignment, and the encoded H.264 metadata before replacing the target file.
7. Review the encoded result at the requested beats:

   ```sh
   scripts/contact_sheet.sh renders/<name>/<name>.mp4 <frame> [frame ...]
   scripts/grab_frames.sh renders/<name>/<name>.mp4 <fps> <seconds>:<label> [...]
   ```

## Alpha and compositing principles

- Do not flatten the Motion Canvas sequence before it reaches FFmpeg's `overlay` filter.
- Use both image inputs at the same resolution and FPS, with explicit start numbers 1 (Blender) and 0 (Motion Canvas).
- Composite alpha first, then convert to `yuv420p` for broad H.264 playback compatibility.
- Do not expect H.264/yuv420p to retain transparency. Preserve the RGBA sequence as the editable overlay master.
- Never silently rescale, drop, or duplicate frames to conceal a mismatch; fail validation and fix the source sequence instead.

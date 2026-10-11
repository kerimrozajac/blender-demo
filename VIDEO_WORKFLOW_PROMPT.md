# Blender + Motion Canvas Video Workflow

Copy the prompt template at the bottom, fill in the `[BRACKETS]`, and send it as one request. This file is the source of truth; follow it directly.

## Goal: complete and verifiable delivery

Deliver a finished video that meets the user's stated requirements. Work efficiently, but treat requested timing, design, framing, and output checks as acceptance criteria rather than assuming a successful render is a successful result.

- Inspect the source `.blend` before animating. Determine whether it has an armature, actions, shape keys, or useful controls; preserve useful geometry/materials. For an unrigged one-piece object, a parent Empty/pivot is a reversible transform-based fallback. Do not imply finger motion or mesh deformation that the source does not support.
- Reuse nearby Blender/Motion Canvas code when it actually fits. Read and understand exact paths, timing, coordinate systems, color management, and output behavior before adapting it.
- Set technical constraints and timing once. Render representative previews/key moments before the full render when framing, camera orientation, typography, or timing is uncertain. Fix issues against the request; avoid unrelated aesthetic redesign.
- Inspect the opening, named text transitions, representative movement, and ending whenever the request calls out those beats. A contact sheet is a fast first pass; inspect individual full-size frames for clipping or transparency issues.
- Verify exact frame counts, filename indexing, dimensions, FPS, duration, codec, audio presence, and alpha-bearing overlay PNGs. Do not trust the Motion Canvas UI's last-frame label or an incomplete folder count.
- Keep both image sequences until the final MP4 has been encoded and verified. Render to separate Blender and Motion Canvas directories, then composite matching frame indices one-to-one.
- Do not write image-measurement scripts without a concrete need. Visual inspection and metadata checks are the default; add deeper analysis only to resolve a real uncertainty.
- Rerun only a failed stage after a fix. Do not wipe prior output to save time; clear only an explicitly scoped sequence before an intentional rerender.

## Workspace facts

- Root: `blender-demo/`. Blender scene builders in `blender/`, shared Motion Canvas workspace/source in `my-animation/`, workflow helpers in `scripts/`.
- Canonical per-project output: `renders/<name>/scene.blend`, `blender-frames/`, `motion-canvas/`, `<name>.mp4`, and optional `review-frames/`. Keep source code out of render-output folders. The existing `hand.blend` remains at the root because the current scene script refers to it; leave older root-level `.blend` files in place unless every reference is deliberately migrated.
- Use one lowercase kebab-case `<name>` for the Blender script, Motion Canvas entry/scene, render directory, and final video.
- New source assets can go in `assets/<name>/`; leave legacy root-level `.blend` assets where existing projects expect them and pass their paths explicitly.
- Keep reusable guidance in `VIDEO_WORKFLOW_PROMPT.md` and task-specific agent skills in `.github/skills/<skill-name>/SKILL.md`.
- Blender 5.2: `/Applications/Blender.app/Contents/MacOS/Blender`. Always run `--background --factory-startup --python blender/<name>.py` so the user's open Blender is untouched.
- Motion Canvas dependencies are installed. Run npm commands from `my-animation/` (or use `--prefix my-animation`); the workspace root has no package manifest, so installing from the wrong directory can put dependencies in an ancestor project. The dev server normally runs at `http://localhost:9000/` (in the user's terminal); run `npm start` in `my-animation/` only if it doesn't respond. Type-check with `npx tsc --noEmit --pretty false` in `my-animation/`.
- Local fonts: `@fontsource/oswald` (condensed, weights 200–700, no italic files), `@fontsource/nunito`, `@fontsource/space-grotesk` (weights 300–700), `@fontsource/rye` (Western display, weight 400), `@fontsource/bungee`, and `@fontsource/fredoka`. Import CSS for an installed weight. Await `document.fonts.load(...)` before measuring or exporting animated text. Install font packages from `my-animation/`; if Vite cannot resolve a newly installed font, restart the dev server so it rebuilds its dependency graph.
- ffmpeg/ffprobe: `my-animation/node_modules/@ffmpeg-installer/darwin-arm64/ffmpeg` and `@ffprobe-installer/darwin-arm64/ffprobe`. `scripts/finish_video.sh` finds them automatically.
- Speed reference at 640×480: Blender Eevee ≈ 0.4–0.5 s/frame (144 frames rendered in ≈ 71 s). Motion Canvas exports 144 moderately textured frames in a few seconds.
- Motion Canvas browser exports can be throttled if the page is backgrounded or considered hidden. Keep the render page visible/active and poll files until the count is stable and exact; do not rely on the UI ETA or timeline label.

## Folder structure

```text
blender-demo/
├── .github/skills/                 reusable focused agent skills
├── assets/<name>/                  new source images/textures (optional)
├── blender/
│   ├── template_scene.py
│   └── <name>.py                   Blender scene setup and render
├── my-animation/
│   └── src/
│       ├── <name>.ts               Motion Canvas project entry
│       └── scenes/<name>.tsx       transparent graphic/text animation
├── renders/<name>/
│   ├── scene.blend
│   ├── blender-frames/frame0001.png …
│   ├── motion-canvas/000000.png …
│   ├── review-frames/             optional contact sheets/stills
│   └── <name>.mp4
├── scripts/                        scaffolding, collection, validation, review
└── VIDEO_WORKFLOW_PROMPT.md
```

The root already contains legacy `.blend` sources and prior projects, so do not bulk-move them. Keep the source project code in the existing shared Motion Canvas workspace; only the rendered intermediates and deliverables are grouped per project.

## Helper scripts

| Script | What it does |
| --- | --- |
| `blender/template_scene.py` | Starter Blender script: render settings, engine/color-management fallbacks, world color, material, lights, front camera, keyframe helper, `--frames` / `--no-render` flags, and canonical output to `renders/<NAME>/scene.blend` plus `blender-frames/frame####.png`. |
| `scripts/new_scene.py <name> [w] [h] [fps] [seconds] [source.py]` | Copies `blender/template_scene.py`, or a closer previous script, to `blender/<name>.py` and sets `NAME`, size, fps, and `FRAME_END`. Does not overwrite. |
| `scripts/new_overlay.py <name> [w] [h] [fps] [seconds]` | Creates `src/<name>.ts`, `src/<name>.meta`, `src/scenes/<name>.meta`, a starter `src/scenes/<name>.tsx`, and registers the project in `vite.config.ts`. Motion Canvas writes to `my-animation/renders/<name>-overlay/`; collect completed frames into `renders/<name>/motion-canvas/` with `scripts/collect_overlay.py`. |
| `scripts/make_grain.py [out.png] [w] [h] [density]` | Writes a speckle-noise RGBA PNG for a distressed print texture (default `my-animation/src/assets/print-grain.png`). |
| `scripts/clear_overlay.sh <name>` | Deletes only PNGs from the selected project's overlay sequence folder before an intentional rerender. Supports canonical and older locations. |
| `scripts/wait_frames.sh <name> <frames> [overlay\|blender] [stable_seconds]` | Polls the canonical folder (or a legacy folder) until it has exactly `<frames>` PNGs and the count stays unchanged. Fails immediately on extra frames. `WAIT_TIMEOUT` defaults to 180. |
| `scripts/count_frames.sh <name> [expected]` | Prints both sequence counts, first and last filenames, and missing frame names for canonical or legacy folders. Exits non-zero on a gap or count mismatch. |
| `scripts/collect_overlay.py <name> [--source PATH] [--frames N] [--replace]` | Validates contiguous, correctly indexed RGBA PNGs and stages a copy into `renders/<name>/motion-canvas/`. Refuses to replace an existing sequence unless `--replace` is explicit. |
| `scripts/render_utils.py` | Shared PNG-header and contiguous-sequence validation used by the collector and finalizer. |
| `scripts/grab_frames.sh <mp4> [fps] <frame:label \| seconds s:label>...` | Extracts zero-based stills to `/tmp/<stem>-check/<label>.png` for full-size review of specific beats. |
| `scripts/finalize_video.py <name> [--fps N] [--frames N] [--output PATH]` | Validates both complete sequences (including dimensions and overlay alpha), composites matching frames, encodes H.264 `yuv420p` without audio to a temporary file, verifies metadata, then publishes the MP4. Finds system or project-bundled ffmpeg/ffprobe. |
| `scripts/finish_video.sh <name> <output.mp4> [fps] [frames]` | Backwards-compatible wrapper around `finalize_video.py`; detects older `my-animation/renders/<name>-blender` / `-overlay` input folders too. |
| `scripts/contact_sheet.sh <video.mp4> <frame> [frame ...]` | Writes a review sheet for selected zero-based MP4 frames to `renders/<name>/review-frames/`. |
| `scripts/prepare_logo_texture.py` | Blender-run CLI for cropping transparent logos, suppressing low-alpha glow, and optionally recoloring a source-image pixel box. |
| `scripts/add_canopy_decal.py` | Blender-run CLI for ray-projecting a UV-mapped logo onto a mesh and parenting it to an animated object. |
| `blender/logo_decal_utils.py` | Shared implementation for logo cleanup and surface-conforming decal creation; imported by both CLIs and scene builders. |

Use the same `<name>` (lowercase kebab-case) for the Blender `NAME`, Motion Canvas project, render folder, and final MP4. Blender frames are one-based (`frame0001.png`); Motion Canvas and encoded MP4 indices are zero-based (`000000.png`, video frame 0). Both image sequences contain exactly `seconds × fps` frames.

## Fast workflow

1. **Inspect and scope.** Inspect the source model/rig/materials and check for a reusable Blender setup. Derive the exact frame count (`seconds × fps`) and account for one-based Blender versus zero-based Motion Canvas frame names.
2. **Blender.** Run `python3 scripts/new_scene.py <name> W H FPS SECONDS [blender/<closest>.py]`. Use the closest proven script if it fits; otherwise use the template. Preview framing and representative motion when uncertain, then render the full sequence. `scripts/wait_frames.sh <name> FRAMES blender` can monitor it.
3. **Motion Canvas while Blender renders.** Run `python3 scripts/new_overlay.py <name> W H FPS SECONDS`, add requested local assets/fonts from `my-animation/`, implement exact beats, and run `npm run build` from `my-animation/`. Keep the browser export tab active and wait for a stable exact frame count.
4. **Collect and composite.** Run `python3 scripts/collect_overlay.py <name> --frames FRAMES` (supply `--source` if needed), then `python3 scripts/finalize_video.py <name> --fps FPS --frames FRAMES`. It validates sequence filenames, size, and alpha before encoding and verifies the MP4 before publishing it.
5. **Inspect and report.** Run `scripts/contact_sheet.sh <output.mp4> FRAME ...` for the opening, named transitions, representative action, and ending. Use `scripts/grab_frames.sh` for full-size stills if needed. Fix request-specific defects, then re-encode and re-inspect. Report the video, Blender scene, intermediate frame paths, and verified specs.

### Reusable Blender logo/decal helpers

Both command-line helpers run inside Blender so they use Blender's bundled Python, `bpy`, and NumPy. Run them from the workspace root; relative paths are workspace-relative.

1. Clean/crop the transparent logo. Pixel boxes use source-image coordinates `(left, top, right, bottom)`:

   ```sh
   /Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
     --python scripts/prepare_logo_texture.py -- \
     --input assets/logo.png --output assets/prepared/logo.png \
     --alpha-threshold 0.31 --alpha-feather 0.66 --padding 3 \
     --recolor-box 640 200 1200 360 --recolor '#E9BE72'
   ```

   Omit `--recolor-box` when artwork colors must stay exactly as supplied. Inspect the source alpha and artwork before choosing a threshold or recolor region; do not assume the transparent margin, glow cutoff, or lettering bounds are the same between logos.
2. Project the prepared PNG over a chosen canopy patch in an existing scene:

   ```sh
   /Applications/Blender.app/Contents/MacOS/Blender --background renders/project/scene.blend \
     --python scripts/add_canopy_decal.py -- \
     --surface CanopyMesh --parent UmbrellaRoot --image assets/prepared/logo.png \
     --name CanopyLogo --center-radius 0.7 --width 0.35 --height 0.22 \
     --radial-offset-degrees 12 --frame 72 --save-as renders/project/scene.blend
   ```

   `--center-radius`, `--width`, and `--height` are in the parent's local coordinates. The camera selects a panel sector; inspect rib geometry and adjust `--radial-offset-degrees` so the whole footprint stays between ribs and inside the panel. Preview representative rotation frames before rendering the full sequence. The decal is parented to the moving object; it does not use a screen-space overlay.
3. Keep the source material and UVs untouched. The helper creates a separate, UV-mapped mesh sampled against the canopy with local-space ray casts. Use a small surface offset to prevent z-fighting; large offsets can make the print look like it floats. Inspect for raycast holes, panel-edge clipping, visible seams, and legibility at final output size.
4. For generated Blender images, set the color space **before** writing `image.pixels`; changing it after `foreach_set` can reset the pixel buffer. Convert a requested sRGB hex to linear before writing pixels. Pack the image into the `.blend` when portability matters.

## Blender notes

- `image_settings.media_type = 'IMAGE'` must be set before `file_format = 'PNG'` (Blender 5.2 defaults to video output).
- Engine: assign `BLENDER_EEVEE`, fall back to `BLENDER_EEVEE_NEXT` on `TypeError`. Turn Eevee raytracing off for flat/poster looks.
- In background mode, dynamic enums such as `view_transform` read back as `['NONE']`. Assign inside `try/except TypeError`; the error message lists the real options (`enum_choices()` in the template does this).
- Use the **Standard** view transform for saturated, graphic colors. The default AgX dulls bright yellows and makes them look brown.
- Find shader nodes by `type` (`BSDF_PRINCIPLED`, `BACKGROUND`), never by name. Set colors on node inputs, converted from sRGB hex to linear (`srgb_to_linear()` in the template).
- A world color is a solid background. For subtle grain, mix two close colors with a Noise Texture (scale ~80) driven by `Window` coordinates.
- Keep paper-grain ramp colors close together. Large luminance differences make Noise Texture scale 80 look mottled rather than subtle.
- For glossy spheres, a Principled material around roughness `0.05–0.1`, moderate coat, smooth UV-sphere shading, a large area key, soft fill, and a small point glint produces a readable highlight quickly in Eevee.
- An orthographic camera at `(0, -D, 0)` with `ortho_scale = 8` frames an 8-unit vertical span at 640×480. For strict left/right compositions, key the subject around negative X positions and keep its radius clear of X=0.
- Rounded edges: a Bevel modifier (small width, 3 segments) plus `bpy.ops.object.shade_auto_smooth()`.
- Front camera: location `(0, -D, 0)`, rotation `(90°, 0, 0)`. Rotation X = 0 looks straight down. Blender +Z is up on screen.
- Camera shake: add a few keyframes of small location/rotation offsets (≈0.1 units, ≈1°) over 6–10 frames around the impact, returning to the base pose.
- Exaggerated motion: dense keyframes with absolute Euler values that keep increasing for spins (e.g. 0 → 1100°), plus an overshoot key past the target before settling.
- Multi-part subjects: parent to an empty and animate the empty. For tracking cameras, use a `TRACK_TO` constraint on a keyed empty.
- For squash-and-stretch, key both location and scale tightly around impact: normal scale before impact, wide/short at contact, narrow/tall on release, then return to `(1,1,1)`. `AUTO_CLAMPED` Bezier handles prevent obvious overshoot between these keys.
- In Blender 5.2 layered actions, `action.fcurves` may be absent. If interpolation must be changed, fall back to `action.layers[0].strips[0].channelbag(action.slots[0]).fcurves`.
- `World.use_nodes` / `Material.use_nodes` deprecation warnings are harmless.
- Frames are written as `frame0001.png`…; preview stills are named `preview####.png`. Keep previews out of sequence folders: the finalizer rejects unexpected PNGs rather than deleting them silently.

## Motion Canvas notes

- **Coordinates: the origin is the frame center and +y points DOWN.** On a 480-px-tall frame, y = −240 is the top edge and +240 the bottom. "Drops in from above" means starting at a negative y. This is the opposite of Blender.
- Meta file: `background: null`, size, `preview.fps` and `rendering.fps` both set, exporter `@motion-canvas/core/image-sequence` with `fileType: image/png`. `new_overlay.py` writes it correctly.
- `makeProject({name})` sets the output folder: `my-animation/renders/<name>/000000.png`… (`new_overlay.py` names the project `<name>-overlay`).
- Exact frame count: for a 6 s / 24 fps scene, the expected sequence is `000000.png` through `000143.png` (144 frames). This project rendered all 144 with its timeline ending at `DURATION - 1 / FPS`; exporter/timeline boundaries can be easy to misread, so count the PNGs rather than trusting the UI's last-frame label. Use `scripts/wait_frames.sh` / `scripts/count_frames.sh` or `find` to verify `SECONDS × FPS`.
- Transparency: set the project background to `null` and export PNGs with alpha. Verify the actual PNG IHDR/channel format; a preview checkerboard is not sufficient. If the design has a continuously visible border, frame 0 and the last frame will have non-transparent pixels by design—verify that an alpha channel exists, not that the whole frame is transparent. Elements that should not yet appear should start at `opacity={0}` or off-screen.
- Italic from a non-italic font: wrap the text in a `Node` with `skew={[-14, 0]}`.
- Horizontal stretch: animate `scale.x` (e.g. 1.5 → 1.15 → 1).
- Distressed print texture: put the text and an `<Img src={grain}>` in a `Node` with `cache`, and give the Img `compositeOperation={'destination-out'}` and opacity ~0.4–0.6. Import images with `import grain from '../assets/print-grain.png';`. When the same grain is used in multiple cached nodes, create it with a function such as `const grainStamp = () => <Img ... />`; do not reuse one JSX node instance under multiple parents.
- Strict split layout at 640×480: the boundary after a 45% left column is Motion Canvas `x = -32`. Place a thin divider near that value, keep the subject on the Blender left side, and left-align typography just inside the right column. Long lines need roughly 30–34 px Space Grotesk at this resolution.
- Horizontal strip breakup: duplicate the phrase in several cached nodes, vertically offset each copy, mask each with a short `Rect` using `destination-in`, then animate alternating strip nodes left/right. Hide the source phrase after the strips leave.
- Left-to-right text assembly can be made reliably with a cached text node plus a white `Rect` using `destination-in`; animate the mask width from 0 to the required column width.
- Stroke reveal: `Circle`/`Line` with `end={0}`, then animate `end` to 1. Radial lines shooting out: a group of short `Line`s whose parent `scale` is animated outward.
- Graphic wipes: thick rotated `Rect`s moved across the frame with `linear` easing over ~0.3–0.4 s, hidden afterwards.
- Easing: `easeOutBack` gives overshoot on position or scale, `easeOutExpo` a hard slam, `easeInCubic`/`linear` fast exits. Never use a back ease on opacity, because it overshoots above 1.
- To keep overlay graphics around a moving Blender subject roughly synced, convert the subject's screen position once (Blender camera-view x/y in 0–1 → MC x = (x − 0.5)·W, y = (0.5 − y)·H) and key the same beats. Approximate is fine.
- Oswald 700 at ~74 px fits about 10 condensed characters on a 640-wide frame.
- A full-frame grain image inside a cached text node can extend that node's compositing bounds. Keep masks explicit and verify one frame during strip transitions for residual fragments.

## Standalone image-led Motion Canvas video (burger learnings)

Use this path when the requested animation is made entirely in Motion Canvas from an existing image; do not create a Blender render or composite an unnecessary second sequence.

**Project and source**
- Add a dedicated project entry (`src/<name>.ts` importing `./scenes/<name>?scene`), matching `.meta` (canvas size, preview/render FPS, image-sequence exporter), and register the entry in `vite.config.ts`. Keep other projects/scenes intact.
- For an image in the workspace root imported by `src/scenes/<name>.tsx`, a relative import such as `import photo from '../../../photo.webp';` lets Vite bundle that exact source image. Run `npm run build` from `my-animation/` to catch TypeScript, import, and Vite errors before rendering.
- To cover a canvas without distorting an image, calculate a cover fit: `scale = max(canvasWidth / imageWidth, canvasHeight / imageHeight)`. Size the `Img` to the scaled image dimensions, center it, and let the canvas clip the excess. For example, 300×450 into 480×640 becomes 480×720, cropping 40 px from the top and bottom. If the image itself is animated above 100%, ensure the cover fit still extends beyond every canvas edge at the peak scale.
- Add a display font as a project dependency from `my-animation/` and import its CSS in the scene (for Rye: `@fontsource/rye`, `@fontsource/rye/400.css`). Await `document.fonts.load(...)` before measuring text or rendering so layout uses the intended face, not a fallback. Measure `Txt.width()` after fonts load and cap its scale to the safe width.

**Animation and framing**
- For discrete image pops, drive scale from scene time with `useTime()` and a small `update(t)` loop; define the three start times explicitly and use short eased attack/settle segments with a slight undershoot. This stays deterministic during frame export and avoids timeline drift.
- Keep burst strokes in separate `Node`s from the photo. Closed, tapered `Line` polygons make punchy rays; animate each burst's opacity and scale only during the matching pop window, then return opacity to zero. Place rays just outside the important subject silhouette.
- Put every border component (edge shapes, drips, and red accents) under one parent `Node` to control overall opacity consistently. A low group opacity such as `0.15` preserves the image underneath. A slow circular drift can be calculated per frame as `x = cos(t * speed) * radius`, `y = sin(t * speed) * radius`, with a very small sinusoidal rotation; keep the orbit/angle small enough that the border stays near the canvas edges. In the 6-second burger scene, `speed = Math.PI / 3`, a 2.5 px orbit radius, and ±1.5° rotation completed one subtle circular cycle without revealing empty edges.
- A practical stagger for a two-line title is to start the second word 0.5 s after the first, animate the first from left and second from right, then settle both to measured final positions. Keep title text above the image only where the composition allows, and let it hold for the remainder.

**Render, review, and encode**
- Open `http://localhost:9000/src/<name>` and use the Motion Canvas **Render** button to export the sequence. Navigate/reload after source changes so the browser runs the current build. Confirm exactly `SECONDS × FPS` files before encoding.
- Inspect the beginning, each explicitly timed movement (one frame near its peak), and the final frame when the request requires beat-level review. This catches title timing, missed bursts, clipping, and a border that is too strong or too faint.
- `scripts/finish_video.sh` expects both Blender frames and a separate overlay, so it is not the right encoder for an image-led scene rendered as a complete frame. Encode that Motion Canvas sequence directly with the local FFmpeg binary, e.g.:

```bash
my-animation/node_modules/@ffmpeg-installer/darwin-arm64/ffmpeg \
  -y -v error -framerate 24 -start_number 0 \
  -i my-animation/renders/<name>/%06d.png -frames:v 144 \
  -c:v libx264 -preset slow -crf 17 -pix_fmt yuv420p \
  -movflags +faststart -an renders/<name>/<name>.mp4
```

- Verify the actual video with local `ffprobe -count_frames`: check `codec_name=h264`, requested width/height, `avg_frame_rate`, `nb_read_frames`, duration, pixel format, and no audio stream. Image-sequence count alone is not proof of encoded frame count or duration.

## Composite and encode (what `finish_video.sh` runs)

Prefer `python3 scripts/finalize_video.py <name> --fps FPS --frames FRAMES`. It validates the sequence indices/dimensions and alpha, composites Blender frame N with Motion Canvas frame N−1, then verifies the temporary MP4 before publishing it. If FFmpeg must be run manually, preserve alpha blending:

```bash
ffmpeg -framerate FPS -start_number 1 -i renders/<name>/blender-frames/frame%04d.png \
  -framerate FPS -start_number 0 -i renders/<name>/motion-canvas/%06d.png \
  -filter_complex "[0:v][1:v]overlay=0:0:format=auto:shortest=1,format=yuv420p" \
  -c:v libx264 -preset medium -crf 18 -r FPS -movflags +faststart -an renders/<name>/<name>.mp4
```

Blender frame N pairs with Motion Canvas frame N−1. H.264 has no alpha, so any transparency belongs in the intermediate PNG sequences. Render both sequences at the final resolution and frame count; never rescale one to fit the other.

For a Motion Canvas-generated opaque background behind a Blender subject rendered with transparent film, pass `--overlay-behind-subject` to `scripts/finalize_video.py`. It places the Motion Canvas sequence underneath the Blender RGBA frames; the default order remains Motion Canvas over Blender.

For a 6 s / 24 fps job, the required sequences are Blender `frame0001.png`…`frame0144.png` and overlay `000000.png`…`000143.png`. Verify H.264, requested dimensions, `avg_frame_rate=24/1`, exactly 144 decoded frames, `duration=6.000000`, no audio streams, and an RGBA overlay sequence. Do not require first/last overlay alpha to be all zero when the design intentionally includes a continuous border. When a requested transition is not in the contact sheet, use `scripts/grab_frames.sh` with a seconds spec such as `1.8s:phrase2`.

## Lessons from `hey-whats-up` (640×480, 8 s)

- The source hand was one 50k-polygon mesh with a useful existing material but no armature, action, or separate finger controls. Inspect before building; a wrist-area Empty pivot gave a reversible readable wave without damaging the source mesh. The mesh's original quaternion/orientation determined the palm-facing camera axis, so an assumed front view would have shown the wrong side.
- Preview the full camera framing and pivot before committing to all frames. The first hand pose/orientation and pivot needed correction; a model can be fully present in the scene and still be cropped or turned away from the camera.
- For a camera-filling orthographic gradient backdrop, use explicit UVs sized to the camera's visible frame. A generic object-coordinate gradient did not guarantee the requested colors at the frame edges. Confirm both endpoints in a rendered preview.
- Blender's output frames start at 1 while Motion Canvas exports from 0. Composite with both explicit `-start_number` values; do not shift animation timing to compensate for filenames.
- Motion Canvas titles use project-local font packages. Install from `my-animation/`, import each required font weight, await `document.fonts.load(...)` before text measurement, and restart Vite after a font dependency change if the existing server cannot resolve it.
- Browser export speed fell sharply while its page was hidden. Keep the tab active. Do not start collecting/compositing merely because the expected count appears during an active export; wait for the UI to finish and then confirm the count is exact and stable.
- The design's bubbly border remains visible in the first and final overlay frames. That is correct: these are alpha-bearing RGBA frames with bubbles over transparency, not empty frames. Alpha is preserved during the FFmpeg overlay operation; the final H.264 video is opaque by design.
- Inspect the rendered video, not only the two input sequences. A nine-frame contact sheet caught composition/timing, then the beginning, transitions, action, and final frame were checked against the requested beats.
- Final delivery was verified as 640×480, H.264, yuv420p, 24 FPS, 192 decoded frames, 8.000 seconds, and no audio. Keep the intermediate Blender RGB frames and Motion Canvas RGBA sequence alongside the MP4 for revisions.

## Lessons from `represent-vertical` (480×640, 5 s)

Reusable reference scripts: `blender/represent-vertical.py` (glossy tetrahedrons, ortho vertical camera) and `my-animation/src/scenes/represent-vertical.tsx` (drifting speech bubbles, pop-in + sweep text).

**Setup**
- MCP: `.cursor/mcp.json` uses `mcpServers`; VS Code needs `.vscode/mcp.json` with top-level `servers` and `"type": "stdio"`. The Blender MCP is optional; headless Blender scripts did all the work.
- The current template writes Blender output to `renders/<name>/blender-frames`; Motion Canvas exports to `my-animation/renders/<name>-overlay/`. Use `scripts/collect_overlay.py` to stage it under `renders/<name>/motion-canvas/`. Older completed projects may use legacy paths; the finalizer detects them or accepts explicit input paths.
- `scripts/finalize_video.py` supports custom sequence locations with `--blender-frames` and `--overlay-frames`; it validates the paths and uses ffprobe `-count_frames` before publishing.
- Fonts not installed (e.g. Poppins) come from `npm i @fontsource/<font>` in `my-animation/` (Poppins has 800.css). Import `@fontsource/poppins/800.css`.
- Start the dev server with `npm start` in `my-animation/` (async), wait ~6 s, and curl `localhost:9000/src/<name>` for 200. Stop it afterwards: `lsof -ti :9000` then `kill <pid>` (no pkill, no `kill $(...)`).
- macOS `sed -i` needs `-i ''` and is fragile with multiline edits. Use python or the edit tool.

**Blender (5.x)**
- Tetrahedron: `from_pydata` with verts (1,1,1),(1,-1,-1),(-1,1,-1),(-1,-1,1) and faces (0,1,2),(0,3,1),(0,2,3),(1,3,2). Add a Bevel modifier (width 0.14, 6 segments, limit NONE) and smooth shading for a soft glossy look.
- Glossy Principled: roughness 0.12, metallic 0.35, coat weight 1. Three area lights (key, rim, top) at 300–600 W with world strength 0.6 gave good reflections on Eevee.
- Ortho vertical camera: `type='ORTHO'`, `ortho_scale=10`, `sensor_fit='VERTICAL'`, placed at y=-12 looking along +y. Vary depth along y and size for dimension; ortho means depth changes only the lighting and overlap, not apparent size.
- Continuous constant-speed spins: key rotation at frame 1 and FRAME_END+1 (so frame 120 does not repeat frame 1), then set every keyframe to LINEAR. In 5.x the action has no `fcurves`; walk `action.layers[].strips[].channelbags[].fcurves`, with a `try: action.fcurves` fallback.
- Full 120-frame Eevee render at 480×640 takes about 1 minute. Run it in the background, then write the overlay meanwhile.
- A two-frame preview (`-- --frames 1,60`) was worth it for checking composition before the full render.

**Motion Canvas**
- Import `Gradient` from `@motion-canvas/2d`, not `core`. A generator that yields needs a return type: `function* (): ThreadGenerator`.
- Per-frame driven animation (many drifting objects): create the nodes in a plain array, write an `update(t)` that sets position/rotation/scale from `useTime()`, and run `yield (function* (): ThreadGenerator { while (true) { update(useTime()); yield; } })();`. Modulo wrap (`PERIOD`) gives endless enter/exit with no keyframes. Drift along a direction and offset on the normal axis.
- Speech bubble: a closed `Line` with `radius`, points rectangle plus a tail triangle on the bottom edge, gradient fill, thin contrasting stroke. Make the tail long enough (about 0.4 × height) or it reads as a blob.
- Do not start text at `opacity(0)` and then reveal it. The font loads lazily, and the first frames render in a serif fallback. Start at `opacity 0.001` and a small scale so the font loads and the canvas is drawn from frame 0. Verify frames around the pop, where this showed up.
- Highlight sweep: a cyan `Txt` in a `<Node cache>` with a skewed gradient `Rect` using `compositeOperation='destination-in'`, animated in x. Put a white glossy-gradient `Txt` with `shadowColor`/`shadowBlur` underneath. Animate `shadowBlur` and `shadowColor` with `tween` for the glow pulse.
- Rendering via browser tools: open the page, click **Render** (button ref changes each load; read the snapshot), then monitor the actual export until the UI completes. Reload the page after every code change before rendering. Overlay alpha: the first and last frames still contain bubbles (continuous border), so some visible pixels are expected; check that the PNG is RGBA and that the overlay is composited over the base render.

**Verification that was enough**
- ffprobe: h264, 480×640, yuv420p, 24/1, 120 frames, 5.000000 s, no audio stream. Overlay PNG pix_fmt `rgba`.
- Look at one contact sheet built with ffmpeg `hstack` (frames 0, 24, 26, 40, 46, 52, 119; all inputs must have equal size) and a crop of the text row for the sweep. Output with `-update 1` for a single image.

## Lessons from `morning-blend` (480×640, 8 s, cup + brick wall + handwriting)

**The "stuck Motion Canvas server" was really a scene bug plus fragile tooling:**
- **Root cause:** a bare `while (!ready) yield;` in a scene (used to wait for a font promise). In Motion Canvas a bare `yield` does NOT end the frame, so it spins synchronously, freezes the browser main thread, and every Playwright/browser-tool call on that page then hangs (one stalled 1800 s). The font promise could never resolve because the loop blocked the event loop.
- **Fix/rule:** wait for fonts with `yield document.fonts.load('600 62px Caveat', 'text');` (yielding a Promise is supported). Never write a busy loop that only does bare `yield` to wait for async work; every loop must advance time via `yield* waitFor(...)` or a tween.
- Secondary causes: the shared browser-tool tabs were reported "(not visible)" and returned "Page not found"; Vite also died when its async shell ended.
- **Export via headless Chrome instead of the shared tabs.** Install `playwright-core` in a temp dir outside the project (`/tmp/mcrender`), launch `executablePath: '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', headless: true`, open `http://localhost:9000/src/<name>`, click the `RENDER` button (`getByRole('button', {name: 'RENDER'})`), then poll the button text (`ABORT` while rendering, `RENDER` when finished). Always run node scripts with a log file and short sleeps; macOS has no `timeout` command. Delete the temp dir afterwards.
- **Server hygiene:** start with `npm start -- --port 9000 --strictPort` from `my-animation/`; verify with `curl -s -o /dev/null -w '%{http_code}' --max-time 8 http://localhost:9000/src/<name>` and `lsof -nP -iTCP:9000 -sTCP:LISTEN`; kill by PID only (no `pkill`); kill it when done. If a page hangs, suspect the scene code first, then restart.
- Motion Canvas image-sequence export writes **frames+1** files (`000000`–`000192` for 192 frames). Delete the extra last file before `collect_overlay.py`.
- `collect_overlay.py` defaults to 640×480: pass `--width 480 --height 640` for vertical videos, and `--replace` when re-collecting.

**Blender 5.2 headless (no MCP connection needed):**
- Binary: `/Applications/Blender.app/Contents/MacOS/Blender -b file.blend --python blender/<name>.py -- --frames 1,73` for previews.
- Engine enum is `BLENDER_EEVEE` (not `_NEXT`). Brick texture offset uses node properties `.offset` / `.offset_frequency`, not sockets. Geometry Nodes groups need both INPUT and OUTPUT Geometry interface sockets. Layered actions have no `action.fcurves`; walk layers/strips/channelbags.
- Missing texture paths in a supplied `.blend`: relink to the textures folder, keeping materials and UVs.
- Unparented rigid meshes: parent each to an Empty pivot and compute `matrix_parent_inverse` after a view-layer update, otherwise parts jump.
- Handwriting on a curved surface: build text as a mesh (font TTF), warp onto a cylinder slightly offset outward, parent to the cup pivot, and reveal left to right with a Geometry Nodes face-delete mask keyed on X. Check readability at final resolution; ink in a small font at 480 px is subtle.
- Always render previews of the opening, settled and final frames before the full render; check for 0-byte frames after the render.

## Lessons from `umbrella-rain` (480×854, 7 s)

- The FBX was supplied at `assets/morning-blend/fonts/umbrella/Umbrella.FBX`, not `assets/umbrella`; resolve known workspace locations rather than moving assets. The FBX also imported a default cube, camera, and light that were not part of the umbrella.
- The FBX kept its UVs and assembly hierarchy but imported every part with one untextured material. Reconnect PBR maps by mesh component: the `Textures_01` component maps cover the connectors, handle, rod, skeleton, springs, cloth, and canopy; `Textures_02` supplies the runner maps and AO. Verify every image path after saving the `.blend`.
- For an imported scaled group, put a reversible tilt Empty beneath a world-origin yaw Empty and set `matrix_parent_inverse` when parenting. This preserves the model's original world transform while keeping the animated yaw axis vertical.
- A fully Motion Canvas background must be composited beneath Blender's transparent RGBA render. `finalize_video.py --overlay-behind-subject` handles that layering while retaining the default overlay-first order for existing projects.
- This Motion Canvas export produced exactly 168 frames (rather than an extra terminal frame). Verify the UI completion state and contiguous indices before collection; inspect the encoded video to confirm the text groups finish revealing and hold through the end.
- For logos with baked outer glow, crop against a measured alpha threshold and remap the remaining alpha ramp rather than placing the original rectangle on the model. Inspect the cropped image itself for transparent margins, correct color channels, and preserved alpha.
- A ray-projected decal follows an animated object when its mesh is parented to the model root, but camera-facing placement is not necessarily panel-centered. Inspect canopy ribs at the intended reveal frame; adjust the local radial angle to the midpoint between rib centerlines and constrain both the tangential width and radial height to one panel.
- Confirm the decal's screen-space bounds and read its high-resolution final-facing frame before a full render. A decal may technically be conformed to the surface yet still cross seams, sit under ribs, or be too small to identify at mobile resolution.
- Factor logo cleanup and conforming decal projection into `blender/logo_decal_utils.py`; use `scripts/prepare_logo_texture.py` and `scripts/add_canopy_decal.py` to reuse the steps without copying scene-specific code. Helper input coordinates are source-image pixels for recoloring and parent-local units for projection.
- Preserve approved motion and scene surfaces during a branding-only revision. Re-render Blender frames after changing the decal, leave an unchanged Motion Canvas sequence staged, composite with the established layer order, and verify the new output under a distinct filename.
- Conforming a separate UV-mapped decal to a canopy with a local-space raycast lets the logo follow the existing parent/rotation without changing umbrella materials or motion. Offset the sampled surface slightly to avoid z-fighting, center the decal between measured rib angles, and check that its radial/tangential footprint stays within one panel.
- For transparent source logos with baked glow, crop around the artwork's alpha and remap low alpha to zero. In Blender, set a generated image's color space before writing `image.pixels`; changing it afterwards can reset the pixel buffer. Convert exact sRGB brand colors to linear values before storing them in image pixels.

### Lessons from `umbrella-rain` follow-up: text-only canopy, shield background, zoom

Changes: split the logo into `assets/umbrella-rain/skyshield-text.png` and `skyshield-shield.png`; canopy now carries only the text decal; background umbrella icons became vector shields; the real shield PNG fades/scales in at the lower third after the caption; camera `ortho_scale` animates 3.0 → 2.65 linearly over frames 1–168. Published as `the-rain-never-bothered-me-anyway-shield.mp4`; the prior sequences are archived in `renders/umbrella-rain/archive/logo-v1/`.

- Split a logo with `scripts/split_logo.py` (run in Blender; no PIL in the venv). It finds the topmost empty row band in the alpha channel, keeps original RGB, removes the low-alpha glow, remaps alpha, and crops with padding. Always view each output over the project background; a preview of a large PNG scaled by height can look cropped, so scale by width too.
- Decal height must follow the image aspect ratio (`width * h / w`); the text-only decal is wide and short, so pick `center_radius` toward the canopy rim (48) and width (29) from the measured panel width (~0.765 × radius).
- Animate an orthographic zoom with keyframes on `camera.data.ortho_scale` and LINEAR interpolation; `set_smooth_interpolation(obj, interpolation)` handles Blender 5 slotted actions. Check the opening, midpoint and last frame keep the umbrella in frame (end scale 2.65 leaves ~10% margin).
- `--frames ... --no-render` does not write previews; omit `--no-render` to render them. A stale preview image once looked like a result, so check file times.
- Motion Canvas export overwrites same-named files in `my-animation/renders/<name>-overlay`; archive earlier collected sequences first, then verify new modification times and 168 files. Image imports work via a relative path from `src/scenes` to `assets/`.
- The browser tool's `Render` button is reachable with Playwright `getByRole('button', {name: 'Render', exact: true})` even when the embedded viewport is tiny.
- Stop Vite by PID after export and remove the regenerated `scene.blend1`.

## Mandatory: record lessons after every project
When a project finishes, add a "Lessons from `<name>`" section to this file before reporting completion: what failed, root cause, fix, and any new rule or script flag. Do this every time, even if everything went smoothly (note what worked).

## Prompt template

```text
Create a Blender + Motion Canvas video. Follow VIDEO_WORKFLOW_PROMPT.md: inspect the source, meet the stated timing/specs, render both pipelines, composite, verify, and visually inspect the requested beats. Avoid unrelated redesign.

BLENDER
- Source: [NEW: describe the shape/model] OR [EXISTING .blend: workspace-relative path]
- Look: [colors, materials, background, lighting, style]
- Animation: [movement, timing, rotations, impacts]
- Camera: [framing, lens, movement, shake]

MOTION CANVAS OVERLAY (transparent background)
- Text: [exact lines]
- Typography: [font, weight, size, colors per line, layout]
- Graphics: [shapes and their animation, optional]
- Text animation: [entrance, hold, exit, timing]
- Placement: [where in the frame; text may overlap the subject]

OUTPUT
- [WIDTH]×[HEIGHT], [SECONDS] s, [FPS] fps ([SECONDS × FPS] frames)
- Format: [MP4 H.264 / other]
- Output: [workspace-relative path/NAME.mp4]
- Audio: [none / path]
```

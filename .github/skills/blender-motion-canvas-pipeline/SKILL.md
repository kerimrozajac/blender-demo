---
name: blender-motion-canvas-pipeline
description: Build and deliver animations that combine an inspected Blender scene with a transparent Motion Canvas overlay, using this workspace's source layout and reusable scripts.
---

# Blender + Motion Canvas production

Use this skill when a request needs a Blender render plus separate Motion Canvas graphics/text, then a composited video. Follow [VIDEO_WORKFLOW_PROMPT.md](../../../VIDEO_WORKFLOW_PROMPT.md) for detailed workspace facts and lessons.

## Workspace conventions

- Blender scene-builder scripts: `blender/<name>.py`.
- Shared Motion Canvas project and source: `my-animation/src/<name>.ts` and `my-animation/src/scenes/<name>.tsx`, plus matching `.meta` files and `vite.config.ts`.
- Per-project renders: `renders/<name>/scene.blend`, `blender-frames/frame0001.png`, `motion-canvas/000000.png`, `<name>.mp4`, and optional `review-frames/`.
- Preserve existing root assets and older project outputs. Do not move files just to match the convention if scripts still refer to their current location.
- Use one lowercase kebab-case name everywhere. Keep Blender's 1-based sequence names and Motion Canvas's 0-based names.

## Production steps

1. Inspect the `.blend` before editing: identify the intended subject, materials, armature/actions, shape keys, object orientation, and camera-facing axis. Preserve useful source content. For an unrigged rigid mesh, parent to an Empty near its natural pivot rather than destructively applying a new mesh pose.
   - For a logo/print revision, inspect the supplied image's alpha/artwork, mesh UV/material setup, and the target surface's orientation before deciding how to crop or place the mark.
2. Confirm output size, integer FPS, duration, and exact frame count (`seconds × fps`). Make scene and project metadata agree.
3. Reuse a nearby proven Blender script only after checking its camera, render path, coordinate assumptions, and color management. The template is `blender/template_scene.py`; scaffold with `python3 scripts/new_scene.py <name> W H FPS SECONDS`.
4. Build the Motion Canvas entry/scene with `python3 scripts/new_overlay.py <name> W H FPS SECONDS`. Install any needed fonts from `my-animation/`, import the exact weight CSS, and await `document.fonts.load(...)` before measuring text. Restart Vite after installing fonts if the current server cannot resolve them.
5. Preview uncertain camera framing and animation beats before full rendering. Keep all named elements within safe margins and ensure the main titles do not conflict with the subject unless the design explicitly asks for overlap.
6. Render Blender and Motion Canvas independently. For browser export, keep its tab visible and active; wait for the export UI to finish, then verify a stable exact sequence count.
7. Collect and composite:

   ```sh
   python3 scripts/collect_overlay.py <name> --frames <frame-count>
   python3 scripts/finalize_video.py <name> --fps <fps> --frames <frame-count>
   ```

   Specify `--source` to collect an ambiguous Motion Canvas export folder. Specify `--replace` only when intentionally replacing the existing overlay frames.
8. Inspect the requested beats in the final encoded video, not only the source sequences:

   ```sh
   scripts/contact_sheet.sh renders/<name>/<name>.mp4 0 12 24 48 72 96 120 168 191
   ```

   Use `scripts/grab_frames.sh` for full-size stills at specific times/frames.
9. Report the final video path, the Blender scene path, intermediate sequence paths, and verified output properties. Keep the source sequences until final verification is complete.

## Key lessons

- Do not assume a mesh's local axes or face orientation. A working object can still appear edge-on or cropped; render a preview before the full sequence.
- Reuse `blender/logo_decal_utils.py`, `scripts/prepare_logo_texture.py`, and `scripts/add_canopy_decal.py` for transparent logo cleanup and mesh-conforming decals. These Blender-run helpers keep image processing and ray-projection logic shared rather than duplicated in each scene builder.
- A camera-facing radial direction only selects the approximate canopy sector; it does not guarantee placement between ribs. Inspect rib centerlines at the intended reveal frame, adjust the radial offset, and ensure the decal's full radial/tangential footprint stays inside one panel.
- Transparent source logos may contain a broad low-alpha glow. Inspect/crop against measured alpha, and do not assume logo text bounds or colors. Set a generated image's color space before writing its pixel buffer; changing it afterwards can reset the pixels. Convert explicit sRGB hex colors to linear when modifying Blender image pixels.
- A separate ray-projected decal preserves the underlying material and UVs and follows the model when parented to its root. Use a small surface offset to avoid z-fighting without making the print appear to float. Preview the full-size camera-facing frame and check panel seams, ribs, clipped ray samples, and small-size legibility before rendering all frames.
- For an orthographic backdrop gradient, explicit UV coordinates matching the camera view make endpoint colors predictable.
- Continuous alpha-bearing border art means the first/last overlay frames are not fully transparent. Confirm RGBA channels and composite over the Blender plate; do not treat visible bubbles as an alpha failure.
- `overlay=0:0:shortest=1:format=auto` composites matching frames while using the overlay alpha. The final H.264/yuv420p file is opaque; alpha belongs in the PNG intermediate.
- Do not infer export completion from a frame count that appears while Motion Canvas is still rendering. Wait for its completion state, then check sequence numbering/count again.

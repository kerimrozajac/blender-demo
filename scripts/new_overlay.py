#!/usr/bin/env python3
"""Scaffold a Motion Canvas overlay project and register it in vite.config.ts.

Usage: python3 scripts/new_overlay.py <name> [width] [height] [fps] [seconds]
Creates src/<name>.ts, src/<name>.meta, src/scenes/<name>.meta, src/scenes/<name>.tsx.
Renders land in my-animation/renders/<name>-overlay/ once you click Render at
http://localhost:9000/src/<name>.
"""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "my-animation"

name = sys.argv[1]
width = int(sys.argv[2]) if len(sys.argv) > 2 else 640
height = int(sys.argv[3]) if len(sys.argv) > 3 else 480
fps = int(sys.argv[4]) if len(sys.argv) > 4 else 24
seconds = float(sys.argv[5]) if len(sys.argv) > 5 else 4

src = ROOT / "src"
project_meta = {
    "version": 1,
    "shared": {
        "background": None,
        "range": [0, None],
        "size": {"x": width, "y": height},
        "audioOffset": 0,
    },
    "preview": {"fps": fps, "resolutionScale": 1},
    "rendering": {
        "fps": fps,
        "resolutionScale": 1,
        "colorSpace": "srgb",
        "exporter": {
            "name": "@motion-canvas/core/image-sequence",
            "options": {"fileType": "image/png", "quality": 100, "groupByScene": False},
        },
    },
}

files = {
    src / f"{name}.ts": f"""import {{makeProject}} from '@motion-canvas/core';

import scene from './scenes/{name}?scene';

export default makeProject({{
  name: '{name}-overlay',
  scenes: [scene],
}});
""",
    src / f"{name}.meta": json.dumps(project_meta, indent=2) + "\n",
    src / "scenes" / f"{name}.meta": json.dumps({"version": 1, "timeEvents": [], "seed": 1}, indent=2) + "\n",
    src / "scenes" / f"{name}.tsx": f"""import {{Node, Txt, makeScene2D}} from '@motion-canvas/2d';
import {{all, createRef, easeOutBack, easeOutCubic, useTime, waitFor}} from '@motion-canvas/core';
import '@fontsource/oswald/700.css';

const DURATION = {seconds:g};
const FPS = {fps};

// Origin is the frame center; +y points DOWN. Top of a {height}px frame is y = -{height // 2}.
const LINE1 = 'LINE ONE';
const LINE2 = 'LINE TWO';
const LINE1_Y = -170;
const LINE2_Y = 180;
const FONT = {{fontFamily: 'Oswald', fontWeight: 700, fontSize: 72}};
const SLANT = -14;

export default makeScene2D(function* (view) {{
  const line1 = createRef<Node>();
  const line2 = createRef<Node>();

  view.add(
    <>
      <Node ref={{line1}} x={{-900}} y={{LINE1_Y}} skew={{[SLANT, 0]}} opacity={{0}}>
        <Txt text={{LINE1}} fill={{'#F4E8D0'}} {{...FONT}} />
      </Node>
      <Node ref={{line2}} y={{-600}} skew={{[SLANT, 0]}} opacity={{0}}>
        <Txt text={{LINE2}} fill={{'#E5FF00'}} {{...FONT}} />
      </Node>
    </>,
  );

  yield* waitFor(0.3);
  line1().opacity(1);
  yield* line1().x(0, 0.2, easeOutCubic);
  yield* waitFor(0.5);
  line2().opacity(1);
  yield* line2().y(LINE2_Y, 0.3, easeOutBack);

  yield* waitFor(Math.max(0, DURATION - 2 / FPS - useTime()));
  line1().opacity(0);
  line2().opacity(0);

  yield* waitFor(Math.max(0, DURATION - useTime()));
}});
""",
}

for path, text in files.items():
    if path.exists():
        print(f"exists, skipped: {path.relative_to(ROOT)}")
        continue
    path.write_text(text)
    print(f"created: {path.relative_to(ROOT)}")

vite = ROOT / "vite.config.ts"
config = vite.read_text()
entry = f"'./src/{name}.ts'"
if entry in config:
    print("vite.config.ts already lists it")
else:
    match = re.search(r"project:\s*\[(.*?)\]", config, re.S)
    if not match:
        sys.exit("could not find the project array in vite.config.ts; add it by hand")
    items = [i.strip() for i in match.group(1).split(",") if i.strip()]
    items.append(entry)
    body = "".join(f"\n        {i}," for i in items)
    config = config[: match.start()] + f"project: [{body}\n      ]" + config[match.end() :]
    vite.write_text(config)
    print("registered in vite.config.ts")

print(f"open http://localhost:9000/src/{name} and click Render")

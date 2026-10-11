import '@fontsource/oswald/700.css';
import {Node, Rect, Txt, makeScene2D} from '@motion-canvas/2d';
import {
  all,
  createRef,
  easeInOutCubic,
  easeOutCubic,
  makeRef,
  sequence,
  useTime,
  waitFor,
} from '@motion-canvas/core';

const LINES = [['BEYOND', 'THE'], ['ORDINARY']];
const ACCENT_WORDS = ['ORDINARY'];

const DURATION = 6;
const FPS = 24;
const EXIT_START = 5;

const OFF_WHITE = '#F4F1E8';
const LIME = '#C5FF3D';
const FONT = 'Oswald';
const FONT_SIZE = 72;
const WORD_GAP = 18;
const LINE_SPACING = 68;

const SAFE_LEFT = 96;
const SAFE_BOTTOM = 72;
// Left edge and vertical center of the text block, in scene coordinates (origin at center).
const BLOCK_X = -640 + SAFE_LEFT;
const BLOCK_Y = 360 - SAFE_BOTTOM - FONT_SIZE / 2 - LINE_SPACING / 2;
const EXIT_OFFSET = 70;

export default makeScene2D(function* (view) {
  yield document.fonts.load(`700 ${FONT_SIZE}px ${FONT}`);

  const block = createRef<Node>();
  const masks: Rect[] = [];
  const words: Txt[] = [];
  const allWords = LINES.flat();

  view.add(
    <Node ref={block} position={[BLOCK_X, BLOCK_Y]} scale={0.95}>
      {allWords.map((word, i) => (
        <Rect ref={makeRef(masks, i)} clip>
          <Txt
            ref={makeRef(words, i)}
            text={word}
            fontFamily={FONT}
            fontWeight={700}
            fontSize={FONT_SIZE}
            lineHeight={FONT_SIZE}
            fill={ACCENT_WORDS.includes(word) ? LIME : OFF_WHITE}
            opacity={0}
          />
        </Rect>
      ))}
    </Node>,
  );

  // Left-align each line. Each word sits in its own mask and starts hidden to its left.
  let index = 0;
  LINES.forEach((line, row) => {
    let left = 0;
    for (let i = index; i < index + line.length; i++) {
      const width = words[i].width();
      masks[i].size([width, FONT_SIZE * 1.3]);
      masks[i].position([left + width / 2, (row - (LINES.length - 1) / 2) * LINE_SPACING]);
      words[i].x(-width);
      left += width + WORD_GAP;
    }
    index += line.length;
  });

  // Reveal words one at a time from the left over the first second.
  yield* sequence(
    0.15,
    ...words.map(w => all(w.x(0, 0.7, easeOutCubic), w.opacity(1, 0.5))),
  );

  // Settle the whole block from 95% to 100%, then hold.
  yield* block().scale(1, 0.5, easeInOutCubic);
  yield* waitFor(EXIT_START - useTime());

  // Drift right and fade out during the final second.
  masks.forEach(mask => mask.clip(false));
  yield* sequence(
    0.1,
    ...words.map(w =>
      all(w.x(EXIT_OFFSET, 0.75, easeInOutCubic), w.opacity(0, 0.75, easeInOutCubic)),
    ),
  );

  // The renderer exports both the first and last frame, so end one frame early.
  yield* waitFor(Math.max(0, DURATION - 1 / FPS - useTime()));
});

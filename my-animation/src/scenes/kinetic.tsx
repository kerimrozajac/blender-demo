import '@fontsource/oswald/700.css';
import {Node, Txt, makeScene2D} from '@motion-canvas/2d';
import {
  all,
  createRef,
  easeInCubic,
  easeInOutCubic,
  easeOutCubic,
  makeRef,
  sequence,
  useTime,
  waitFor,
} from '@motion-canvas/core';

const LINES = [
  ['LOREM', 'IPSUM'],
  ['DOLOR', 'SIT', 'AMET'],
];
const ACCENT_WORDS = ['IPSUM', 'AMET'];

const DURATION = 4;
const FPS = 24;

const OFF_WHITE = '#F4F1E8';
const LIME = '#C5FF3D';
const FONT = 'Oswald';
const FONT_SIZE = 84;
const WORD_GAP = 18;
const LINE_SPACING = 88;
const ENTER_OFFSET = 180;
const EXIT_SPREAD = 2.4;

export default makeScene2D(function* (view) {
  yield document.fonts.load(`700 ${FONT_SIZE}px ${FONT}`);

  const block = createRef<Node>();
  const words: Txt[] = [];
  const allWords = LINES.flat();

  view.add(
    <Node ref={block} y={70} opacity={0}>
      {allWords.map((word, i) => (
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
      ))}
    </Node>,
  );

  // Lay words out centered on their lines; remember each resting x.
  const restX: number[] = [];
  let index = 0;
  LINES.forEach((line, row) => {
    const lineWords = words.slice(index, index + line.length);
    const total =
      lineWords.reduce((sum, w) => sum + w.width(), 0) +
      WORD_GAP * (line.length - 1);
    let x = -total / 2;
    for (const w of lineWords) {
      restX.push(x + w.width() / 2);
      w.position([x + w.width() / 2, (row - (LINES.length - 1) / 2) * LINE_SPACING]);
      x += w.width() + WORD_GAP;
    }
    index += line.length;
  });

  // 1 + 2: block rises while words enter from alternating sides.
  words.forEach((w, i) => w.x(restX[i] + (i % 2 ? ENTER_OFFSET : -ENTER_OFFSET)));
  yield* all(
    block().y(0, 0.9, easeOutCubic),
    block().opacity(1, 0.4),
    sequence(
      0.08,
      ...words.map((w, i) => all(w.x(restX[i], 0.7, easeOutCubic), w.opacity(1, 0.5))),
    ),
  );

  // 3: brief scale-up and settle.
  yield* block().scale(1.1, 0.25, easeOutCubic).to(1, 0.4, easeInOutCubic);
  yield* waitFor(0.85);

  // 4: words slide apart (proportional to distance from center) and fade out.
  yield* sequence(
    0.05,
    ...words.map((w, i) =>
      all(
        w.x(restX[i] * EXIT_SPREAD, 0.7, easeInCubic),
        w.opacity(0, 0.6, easeInCubic),
      ),
    ),
  );

  // The renderer exports both the first and last frame, so end one frame early.
  yield* waitFor(DURATION - 1 / FPS - useTime());
});

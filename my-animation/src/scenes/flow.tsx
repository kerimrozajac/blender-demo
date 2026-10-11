import '@fontsource/nunito/800.css';
import {Node, Txt, makeScene2D} from '@motion-canvas/2d';
import {
  all,
  createRef,
  easeInCubic,
  easeInOutCubic,
  easeOutBack,
  easeOutCubic,
  makeRef,
  sequence,
  useTime,
  waitFor,
} from '@motion-canvas/core';

const WORDS = ['GO', 'WITH', 'THE', 'FLOW'];
const ACCENT = 'FLOW';

const DURATION = 10;
const FPS = 24;
const EXIT_START = 8.1;

const NAVY = '#1A2744';
const CORAL = '#F05B50';
const FONT = 'Nunito';
const FONT_SIZE = 46;
const WORD_GAP = 16;
const TOP_Y = -240 + 36 + FONT_SIZE / 2;
const ENTER_DROP = 46;
const EXIT_SPREAD = 28;

export default makeScene2D(function* (view) {
  yield document.fonts.load(`800 ${FONT_SIZE}px ${FONT}`);

  const line = createRef<Node>();
  const words: Txt[] = [];

  view.add(
    <Node ref={line} y={TOP_Y}>
      {WORDS.map((word, i) => (
        <Txt
          ref={makeRef(words, i)}
          text={word}
          fontFamily={FONT}
          fontWeight={800}
          fontSize={FONT_SIZE}
          letterSpacing={1.5}
          fill={word === ACCENT ? CORAL : NAVY}
          opacity={0}
          scale={word === ACCENT ? 0.72 : 1}
        />
      ))}
    </Node>,
  );

  const restX: number[] = [];
  const total =
    words.reduce((sum, word) => sum + word.width(), 0) + WORD_GAP * (words.length - 1);
  let left = -total / 2;
  words.forEach((word, i) => {
    restX.push(left + word.width() / 2);
    word.position([restX[i], ENTER_DROP]);
    left += word.width() + WORD_GAP;
  });

  // "GO", "WITH" and "THE" rise in with a soft bounce. "FLOW" follows,
  // overshooting its scale before it settles.
  yield* sequence(
    0.26,
    ...words.map(word =>
      all(
        word.y(0, 0.72, easeOutBack),
        word.opacity(1, 0.35, easeOutCubic),
        word.scale(1, 0.8, easeOutBack),
      ),
    ),
  );

  yield* waitFor(EXIT_START - useTime());

  // Drift apart and fade. The renderer exports both end frames, so finish early.
  const center = (words.length - 1) / 2;
  yield* all(
    ...words.map((word, i) =>
      all(
        word.x(restX[i] + (i - center) * EXIT_SPREAD, 1.25, easeInOutCubic),
        word.opacity(0, 1.15, easeInCubic),
      ),
    ),
  );
  yield* waitFor(Math.max(0, DURATION - 1 / FPS - useTime()));
});

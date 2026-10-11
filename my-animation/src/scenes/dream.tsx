import '@fontsource/oswald/700.css';
import {Node, Txt, makeScene2D} from '@motion-canvas/2d';
import {
  all,
  createRef,
  easeInCubic,
  easeInOutCubic,
  easeOutBack,
  easeOutCubic,
  sequence,
  useTime,
  waitFor,
} from '@motion-canvas/core';

const WHITE = '#FFFFFF';
const CYAN = '#48F5E9';
const ORANGE = '#FF793F';

const DURATION = 10;
const FPS = 24;

const SWAP_2 = 2.2;
const SWAP_3 = 4.6;
const SWAP_4 = 7.25;
const DISPERSE = 8.75;

const FONT = 'Oswald';
const WEIGHT = 700;
const LINE_GAP = 8;
const WORD_GAP = 16;
const RISE = 52;
const SLIDE = 720;
const ASSEMBLE = 26;
const SPREAD = 64;

const PHRASES: {text: string; fill: string; size: number}[][][] = [
  [
    [{text: 'DREAM', fill: WHITE, size: 92}],
    [
      {text: 'WITHOUT', fill: CYAN, size: 36},
      {text: 'LIMITS', fill: ORANGE, size: 76},
    ],
  ],
  [
    [
      {text: 'MAKE', fill: WHITE, size: 64},
      {text: 'YOUR', fill: CYAN, size: 42},
    ],
    [
      {text: 'OWN', fill: WHITE, size: 38},
      {text: 'PATH', fill: ORANGE, size: 88},
    ],
  ],
  [
    [
      {text: 'GO', fill: WHITE, size: 50},
      {text: 'BEYOND', fill: CYAN, size: 70},
    ],
    [
      {text: 'THE', fill: WHITE, size: 34},
      {text: 'HORIZON', fill: ORANGE, size: 78},
    ],
  ],
  [
    [
      {text: 'THE', fill: WHITE, size: 36},
      {text: 'WORLD', fill: CYAN, size: 82},
    ],
    [
      {text: 'IS', fill: WHITE, size: 36},
      {text: 'YOURS', fill: ORANGE, size: 86},
    ],
  ],
];

export default makeScene2D(function* (view) {
  yield document.fonts.load(`${WEIGHT} 92px ${FONT}`);

  const groups = PHRASES.map(() => createRef<Node>());
  const words: Txt[][] = [];

  PHRASES.forEach((lines, phrase) => {
    const phraseWords: Txt[] = [];
    view.add(
      <Node
        ref={groups[phrase]}
        position={[phrase === 1 ? SLIDE : 0, 0]}
        opacity={phrase === 1 || phrase === 3 ? 0 : 1}
        scale={phrase === 3 ? 0.78 : 1}
        zIndex={phrase}
      >
        {lines.flat().map((word, index) => (
          <Txt
            ref={ref => {
              phraseWords[index] = ref;
            }}
            text={word.text}
            fontFamily={FONT}
            fontWeight={WEIGHT}
            fontSize={word.size}
            lineHeight={word.size}
            letterSpacing={-0.5}
            fill={word.fill}
            opacity={phrase === 0 || phrase === 2 ? 0 : 1}
            shadowColor={'rgba(16, 6, 32, 0.7)'}
            shadowBlur={10}
            shadowOffset={[0, 3]}
          />
        ))}
      </Node>,
    );
    words.push(phraseWords);
  });

  const groupOf = (index: number) => groups[index]();
  const rest: {x: number; y: number}[][] = words.map(() => [] as {x: number; y: number}[]);

  words.forEach((phraseWords, phrase) => {
    const lines = PHRASES[phrase];
    const heights = lines.map(line => Math.max(...line.map(word => word.size)));
    const totalHeight =
      heights.reduce((sum, height) => sum + height, 0) + LINE_GAP * (lines.length - 1);
    let top = -totalHeight / 2;
    let index = 0;
    lines.forEach((line, row) => {
      const widths = line.map((_, offset) => phraseWords[index + offset].width());
      const totalWidth =
        widths.reduce((sum, width) => sum + width, 0) + WORD_GAP * (line.length - 1);
      let left = -totalWidth / 2;
      line.forEach((_, offset) => {
        const word = phraseWords[index + offset];
        const x = left + widths[offset] / 2;
        const y = top + heights[row] / 2;
        rest[phrase].push({x, y});
        word.position([x, y]);
        left += widths[offset] + WORD_GAP;
      });
      index += line.length;
      top += heights[row] + LINE_GAP;
    });
  });

  // Chapter 1 rises into view. The first frame stays empty.
  words[0].forEach((word, index) => word.y(rest[0][index].y + RISE));
  yield* all(
    ...words[0].map((word, index) =>
      all(
        word.position([rest[0][index].x, rest[0][index].y], 0.72, easeOutBack),
        word.opacity(1, 0.4, easeOutCubic),
      ),
    ),
  );

  yield* waitFor(SWAP_2 - useTime());

  // Chapter 2 slides in from the right as chapter 1 leaves to the left.
  yield* all(
    groupOf(0).x(-SLIDE, 0.58, easeInOutCubic),
    groupOf(0).opacity(0, 0.36, easeInCubic),
    groupOf(1).x(0, 0.58, easeInOutCubic),
    groupOf(1).opacity(1, 0.4, easeOutCubic),
  );

  yield* waitFor(SWAP_3 - useTime());

  // Chapter 3 assembles word by word while chapter 2 exits left.
  words[2].forEach((word, index) => word.y(rest[2][index].y + ASSEMBLE));
  yield* all(
    groupOf(1).x(-SLIDE * 0.55, 0.48, easeInOutCubic),
    groupOf(1).opacity(0, 0.32, easeInCubic),
    sequence(
      0.11,
      ...words[2].map((word, index) =>
        all(
          word.position([rest[2][index].x, rest[2][index].y], 0.46, easeOutBack),
          word.opacity(1, 0.3, easeOutCubic),
        ),
      ),
    ),
  );

  yield* waitFor(SWAP_4 - useTime());

  // Chapter 4 scales up, holds, then the words drift apart and fade.
  yield* all(
    groupOf(2).y(-28, 0.4, easeInOutCubic),
    groupOf(2).opacity(0, 0.32, easeInCubic),
    groupOf(3).scale(1, 0.62, easeOutBack),
    groupOf(3).opacity(1, 0.32, easeOutCubic),
  );

  yield* waitFor(DISPERSE - useTime());

  yield* all(
    ...words[3].map((word, index) => {
      const point = rest[3][index];
      const dx = Math.sign(point.x || (index % 2 === 0 ? -1 : 1)) * SPREAD;
      const dy = (index < 2 ? -1 : 1) * SPREAD * 0.72;
      return all(
        word.position([point.x + dx, point.y + dy], 0.85, easeInOutCubic),
        word.opacity(0, 0.78, easeInCubic),
      );
    }),
  );

  yield* waitFor(Math.max(0, DURATION - 1 / FPS - useTime()));
});

import {Circle, Img, Line, Node, Rect, Txt, makeScene2D} from '@motion-canvas/2d';
import {
  all,
  chain,
  createRef,
  delay,
  easeInCubic,
  easeOutBack,
  easeOutCubic,
  linear,
  sequence,
  useTime,
  waitFor,
} from '@motion-canvas/core';
import '@fontsource/space-grotesk/700.css';
import grain from '../assets/think-make-move-grain.png';

const DURATION = 6;
const FPS = 24;

const INK = '#172554';
const CORAL = '#FF5C5C';
const MINT = '#B8F3D4';

// Right 55% starts at x = -32. Text is left-aligned inside that column.
const TEXT_X = -16;
const LINE_A = -17;
const LINE_B = 16;
const DIV_X = -40;
const FONT = {
  fontFamily: 'Space Grotesk',
  fontWeight: 700,
  fontSize: 32,
  letterSpacing: -0.6,
};

const STRIPS = 5;
const STRIP_H = 24;
const STRIP_TOP = -48;

export default makeScene2D(function* (view) {
  const think = createRef<Txt>();
  const inMotion = createRef<Txt>();
  const phrase1 = createRef<Node>();
  const phrase2 = createRef<Node>();
  const phrase3 = createRef<Node>();
  const reveal = createRef<Rect>();
  const divider = createRef<Line>();
  const marks = createRef<Node>();
  const diamond = createRef<Rect>();
  const stripRefs = Array.from({length: STRIPS}, () => createRef<Node>());
  const newRefs = Array.from({length: STRIPS}, () => createRef<Txt>());

  const grainStamp = () => (
    <Img src={grain} width={640} height={480} compositeOperation={'destination-out'} opacity={0.4} />
  );

  view.add(
    <>
      <Line
        ref={divider}
        points={[
          [DIV_X, -190],
          [DIV_X, 190],
        ]}
        stroke={CORAL}
        lineWidth={2}
        end={0}
      />

      <Node ref={marks} x={480} y={-84} opacity={0}>
        <Rect ref={diamond} width={8} height={8} fill={CORAL} rotation={45} />
        <Circle width={8} height={8} x={22} fill={MINT} stroke={INK} lineWidth={1.5} />
        <Rect width={16} height={2} x={48} y={1} fill={INK} />
      </Node>

      <Node ref={phrase1}>
        <Node cache>
          <Txt ref={think} text={'THINK'} x={740} y={LINE_A} offset={[-1, 0]} fill={INK} {...FONT} />
          <Txt
            ref={inMotion}
            text={'IN MOTION'}
            x={740}
            y={LINE_B}
            offset={[-1, 0]}
            fill={INK}
            {...FONT}
          />
          {grainStamp()}
        </Node>
      </Node>

      <Node ref={phrase2} y={480} opacity={0}>
        {stripRefs.map((strip, i) => {
          const bandY = STRIP_TOP + STRIP_H / 2 + i * STRIP_H;
          return (
            <Node ref={strip} y={bandY}>
              <Node cache>
                <Node y={-bandY}>
                  <Txt text={'MAKE'} x={TEXT_X} y={LINE_A} offset={[-1, 0]} fill={INK} {...FONT} />
                  <Txt
                    text={'SOMETHING'}
                    x={TEXT_X}
                    y={LINE_B}
                    offset={[-1, 0]}
                    fill={INK}
                    {...FONT}
                  />
                  <Txt
                    ref={newRefs[i]}
                    text={'NEW'}
                    x={TEXT_X + 206}
                    y={LINE_B}
                    offset={[-1, 0]}
                    fill={CORAL}
                    {...FONT}
                  />
                </Node>
                <Rect width={520} height={STRIP_H} fill={'#000000'} compositeOperation={'destination-in'} />
                {grainStamp()}
              </Node>
            </Node>
          );
        })}
      </Node>

      <Node ref={phrase3} opacity={0}>
        <Node cache>
          <Txt text={'KEEP'} x={TEXT_X} y={LINE_A} offset={[-1, 0]} fill={INK} {...FONT} />
          <Txt
            text={'MOVING FORWARD'}
            x={TEXT_X}
            y={LINE_B}
            offset={[-1, 0]}
            fill={INK}
            {...FONT}
          />
          <Rect
            ref={reveal}
            offset={[-1, 0]}
            x={TEXT_X - 6}
            width={0}
            height={150}
            fill={'#ffffff'}
            compositeOperation={'destination-in'}
          />
          {grainStamp()}
        </Node>
      </Node>
    </>,
  );

  marks().opacity(1);
  yield* all(
    sequence(0.14, think().x(TEXT_X, 0.68, easeOutCubic), inMotion().x(TEXT_X, 0.68, easeOutCubic)),
    marks().x(TEXT_X, 0.62, easeOutCubic),
  );
  yield* waitFor(Math.max(0, 1.8 - useTime()));

  phrase2().opacity(1);
  yield* all(
    phrase1().y(-440, 0.42, easeInCubic),
    phrase2().y(0, 0.5, easeOutCubic),
    marks().x(TEXT_X + 20, 0.42, easeOutCubic),
    marks().y(-48, 0.42, easeOutCubic),
    diamond().rotation(135, 0.42, easeOutCubic),
    delay(
      0.34,
      chain(
        all(...newRefs.map(word => word().scale(1.32, 0.16, easeOutBack))),
        all(...newRefs.map(word => word().scale(1, 0.14, easeOutCubic))),
      ),
    ),
  );
  yield* waitFor(Math.max(0, 3.6 - useTime()));

  phrase3().opacity(1);
  yield* all(
    sequence(
      0.04,
      ...stripRefs.map((strip, i) => strip().x(i % 2 === 0 ? -700 : 740, 0.38, easeInCubic)),
    ),
    delay(0.1, reveal().width(360, 0.78, easeOutCubic)),
    marks().x(TEXT_X + 4, 0.4, easeOutCubic),
    marks().y(-118, 0.4, easeOutCubic),
    diamond().rotation(225, 0.4, easeOutCubic),
  );
  yield* waitFor(Math.max(0, 5.2 - useTime()));

  yield* divider().end(1, 0.62, linear);

  yield* waitFor(Math.max(0, DURATION - 2 / FPS - useTime()));
  phrase1().opacity(0);
  phrase2().opacity(0);
  phrase3().opacity(0);
  marks().opacity(0);
  divider().opacity(0);
  // Hold through the final frame so the export is exactly DURATION * FPS.
  yield* waitFor(Math.max(0, DURATION - useTime()));
});

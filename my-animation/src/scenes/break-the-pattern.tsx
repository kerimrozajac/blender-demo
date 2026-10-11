import {Circle, Img, Line, Node, Rect, Txt, makeScene2D} from '@motion-canvas/2d';
import {
  all,
  createRef,
  easeInCubic,
  easeOutCubic,
  easeOutExpo,
  linear,
  useTime,
  waitFor,
} from '@motion-canvas/core';
import '@fontsource/oswald/700.css';

import grain from '../assets/print-grain.png';

const DURATION = 4;
const FPS = 24;

const IVORY = '#F4E8D0';
const ACID = '#E5FF00';
const IVORY_UNDER = '#D7C4A4';
const ACID_UNDER = '#C6DE00';

const FONT_SIZE = 74;
const TOP_Y = -172;
const BOTTOM_Y = 188;
const SLANT = -14;

const CIRCLE_SIZE = 232;
const LINE_ANGLES = [-78, -36, 8, 46, 92, 138, 168];

export default makeScene2D(function* (view) {
  const rig = createRef<Node>();
  const circle = createRef<Circle>();
  const burst = createRef<Node>();
  const barA = createRef<Rect>();
  const barB = createRef<Rect>();
  const breakLine = createRef<Node>();
  const patternLine = createRef<Node>();
  const spokes = LINE_ANGLES.map(() => createRef<Line>());

  view.add(
    <Node>
      <Rect
        ref={barA}
        width={1100}
        height={34}
        fill={ACID}
        rotation={-34}
        x={-820}
        y={36}
        opacity={0}
      />
      <Rect
        ref={barB}
        width={1100}
        height={48}
        fill={ACID}
        rotation={29}
        x={840}
        y={-48}
        opacity={0}
      />
      <Node ref={rig} position={[0, 52]} opacity={0}>
        <Circle
          ref={circle}
          size={CIRCLE_SIZE}
          stroke={IVORY}
          lineWidth={2.5}
          end={0}
          lineCap={'butt'}
        />
        <Node ref={burst} opacity={0}>
          {LINE_ANGLES.map((angle, index) => {
            const rad = (angle * Math.PI) / 180;
            const inner = 128;
            const outer = 156;
            return (
              <Line
                ref={spokes[index]}
                points={[
                  [Math.cos(rad) * inner, Math.sin(rad) * inner],
                  [Math.cos(rad) * outer, Math.sin(rad) * outer],
                ]}
                stroke={IVORY}
                lineWidth={3}
                end={0}
                lineCap={'butt'}
              />
            );
          })}
        </Node>
      </Node>
      <Node
        ref={breakLine}
        cache
        opacity={0}
        x={-860}
        y={TOP_Y}
        scale={[1.48, 1]}
        skew={[SLANT, 0]}
      >
        <Txt
          text={'BREAK THE'}
          fontFamily={'Oswald'}
          fontWeight={700}
          fontSize={FONT_SIZE}
          letterSpacing={-1.5}
          fill={IVORY_UNDER}
          x={3}
          y={2}
        />
        <Txt
          text={'BREAK THE'}
          fontFamily={'Oswald'}
          fontWeight={700}
          fontSize={FONT_SIZE}
          letterSpacing={-1.5}
          fill={IVORY}
        />
        <Img
          src={grain}
          width={520}
          height={130}
          compositeOperation={'destination-out'}
          opacity={0.62}
        />
      </Node>
      <Node
        ref={patternLine}
        cache
        opacity={0}
        y={-460}
        x={0}
        skew={[SLANT, 0]}
      >
        <Txt
          text={'PATTERN.'}
          fontFamily={'Oswald'}
          fontWeight={700}
          fontSize={FONT_SIZE + 6}
          letterSpacing={-1.5}
          fill={ACID_UNDER}
          x={-3}
          y={2}
        />
        <Txt
          text={'PATTERN.'}
          fontFamily={'Oswald'}
          fontWeight={700}
          fontSize={FONT_SIZE + 6}
          letterSpacing={-1.5}
          fill={ACID}
        />
        <Img
          src={grain}
          width={540}
          height={140}
          compositeOperation={'destination-out'}
          opacity={0.62}
        />
      </Node>
    </Node>,
  );

  yield* all(
    (function* () {
      yield* waitFor(0.05);
      rig().opacity(1);
      yield* all(
        circle().end(1, 0.14, easeOutCubic),
        rig().position([0, -25], 0.38, easeOutCubic),
      );
      yield* waitFor(0.74);
      yield* rig().position([122, -16], 0.12, easeInCubic);
      yield* waitFor(0.08);
      yield* rig().position([68, -4], 0.28, easeInCubic);
      yield* rig().position([14, 2], 0.26, easeInCubic);
      yield* rig().position([-26, 14], 0.16, easeOutCubic);
      yield* rig().position([0, 0], 0.28, easeOutCubic);
    })(),
    (function* () {
      yield* waitFor(1.2);
      burst().opacity(1);
      yield* all(
        burst().scale(3.6, 0.2, easeOutCubic),
        ...spokes.map(spoke => spoke().end(1, 0.06, easeOutCubic)),
      );
      burst().opacity(0);
    })(),
    (function* () {
      yield* waitFor(1.42);
      barA().opacity(1);
      yield* barA().x(840, 0.36, linear);
      barA().opacity(0);
    })(),
    (function* () {
      yield* waitFor(1.58);
      barB().opacity(1);
      yield* barB().x(-840, 0.36, linear);
      barB().opacity(0);
    })(),
    (function* () {
      yield* waitFor(0.3);
      breakLine().opacity(1);
      yield* all(
        breakLine().x(0, 0.13, easeOutExpo),
        breakLine().scale.x(1.16, 0.13, easeOutCubic),
      );
      yield* breakLine().scale.x(1, 0.07, easeOutCubic);
    })(),
    (function* () {
      yield* waitFor(1.96);
      patternLine().opacity(1);
      yield* patternLine().y(BOTTOM_Y + 28, 0.14, easeOutCubic);
      yield* patternLine().y(BOTTOM_Y, 0.08, easeOutCubic);
    })(),
    (function* () {
      yield* waitFor(3.56);
      yield* all(
        breakLine().y(TOP_Y - 78, 0.16, linear),
        breakLine().x(-48, 0.16, linear),
        patternLine().y(BOTTOM_Y + 78, 0.16, linear),
        patternLine().x(52, 0.16, linear),
      );
      breakLine().opacity(0);
      patternLine().opacity(0);
      rig().opacity(0);
      burst().opacity(0);
      barA().opacity(0);
      barB().opacity(0);
    })(),
  );

  yield* waitFor(Math.max(0, DURATION - 1 / FPS - useTime()));
});

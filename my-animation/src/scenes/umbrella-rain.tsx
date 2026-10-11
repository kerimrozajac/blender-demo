import {Gradient, Circle, Img, Line, Node, Rect, Txt, makeScene2D} from '@motion-canvas/2d';
import {
  all,
  createRef,
  easeInOutCubic,
  easeOutCubic,
  ThreadGenerator,
  useTime,
  waitFor,
} from '@motion-canvas/core';
import '@fontsource/oswald/700.css';
import shieldLogo from '../../../assets/umbrella-rain/skyshield-shield.png';

const WIDTH = 480;
const HEIGHT = 854;
const DURATION = 7;
const IVORY = '#FFF3DC';
const GOLD = '#E9BE72';
const RAIN_BLUE = '#7196B5';
const MIST_BLUE = '#B9D5E8';
const FONT = 'Oswald';

type RainIcon = {
  ref: ReturnType<typeof createRef<Node>>;
  x: number;
  y: number;
  speed: number;
  size: number;
  alpha: number;
  rotation: number;
  phase: number;
  color: string;
  umbrella: boolean;
};

function positiveModulo(value: number, period: number) {
  return ((value % period) + period) % period;
}

function rng(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let value = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    value = (value + Math.imul(value ^ (value >>> 7), 61 | value)) ^ value;
    return ((value ^ (value >>> 14)) >>> 0) / 4294967296;
  };
}

export default makeScene2D(function* (view): ThreadGenerator {
  yield document.fonts.load('700 52px Oswald', 'the rain never bothered me anyway.');

  const random = rng(41);
  const icons: RainIcon[] = [];
  const iconCount = 48;
  for (let index = 0; index < iconCount; index++) {
    const column = index % 6;
    const row = Math.floor(index / 6);
    const ref = createRef<Node>();
    icons.push({
      ref,
      x: -250 + column * 100 + (row % 2) * 50 + (random() - 0.5) * 26,
      y: -456 + row * 116 + (column % 2) * 36 + (random() - 0.5) * 28,
      speed: 15 + random() * 8,
      size: 0.55 + random() * 0.38,
      alpha: 0.16 + random() * 0.14,
      rotation: (random() - 0.5) * 18,
      phase: random() * Math.PI * 2,
      color:
        index % 13 === 0
          ? GOLD
          : index % 11 === 0
            ? IVORY
            : index % 3 === 0
              ? MIST_BLUE
              : RAIN_BLUE,
      umbrella: index % 4 === 0,
    });
  }

  const before = createRef<Node>();
  const never = createRef<Node>();
  const bothered = createRef<Node>();
  const rest = createRef<Node>();
  const neverWord = createRef<Txt>();
  const brandShield = createRef<Img>();

  const measure = document.createElement('canvas').getContext('2d');
  if (!measure) throw new Error('Canvas text measurement is unavailable');
  measure.font = '700 52px Oswald';
  const beforeWidth = measure.measureText('the rain').width + 8;
  const neverWidth = measure.measureText('never').width + 5;
  const firstGap = 12;
  const firstWidth = beforeWidth + firstGap + neverWidth;
  measure.font = '700 43px Oswald';
  const botheredWidth = measure.measureText('bothered').width + 5.6;
  const restWidth = measure.measureText('me anyway.').width + 7;
  const secondGap = 15;
  const secondWidth = botheredWidth + secondGap + restWidth;

  view.add(
    <>
      <Rect
        width={WIDTH}
        height={HEIGHT}
        fill={
          new Gradient({
            type: 'linear',
            from: [0, -HEIGHT / 2],
            to: [0, HEIGHT / 2],
            stops: [
              {offset: 0, color: '#142536'},
              {offset: 0.52, color: '#1A3045'},
              {offset: 1, color: '#142536'},
            ],
          })
        }
      />
      <Circle
        x={-34}
        y={76}
        width={560}
        height={690}
        fill={'rgba(51,78,104,0.11)'}
      />
      {icons.map((icon, index) => (
        <Node
          ref={icon.ref}
          opacity={icon.alpha}
          scale={icon.size}
          rotation={icon.rotation}
          key={`rain-icon-${index}`}
        >
          {icon.umbrella ? (
            <>
              <Line
                points={[
                  [0, -27],
                  [13, -22],
                  [22, -20],
                  [22, -4],
                  [18, 10],
                  [9, 20],
                  [0, 27],
                  [-9, 20],
                  [-18, 10],
                  [-22, -4],
                  [-22, -20],
                  [-13, -22],
                ]}
                closed
                radius={5}
                fill={icon.color}
                stroke={icon.color}
                lineWidth={1}
                lineJoin={'round'}
              />
              <Line
                points={[
                  [0, -19],
                  [0, 17],
                ]}
                stroke={'rgba(20,37,54,0.38)'}
                lineWidth={1.8}
                lineCap={'round'}
              />
            </>
          ) : (
            <>
              <Line
                points={[
                  [0, -22],
                  [-8, -10],
                  [-15, 1],
                  [-17, 8],
                  [-15, 15],
                  [-10, 20],
                  [-3, 22],
                  [3, 22],
                  [10, 20],
                  [15, 15],
                  [17, 8],
                  [15, 1],
                  [8, -10],
                ]}
                closed
                radius={6}
                fill={icon.color}
                stroke={icon.color}
                lineWidth={1}
                lineJoin={'round'}
              />
              <Line
                points={[
                  [-7, 7],
                  [-5, 1],
                  [-1, -5],
                ]}
                stroke={'rgba(255,243,220,0.48)'}
                lineWidth={1.6}
                lineCap={'round'}
              />
            </>
          )}
        </Node>
      ))}
      <Node ref={before} x={-firstWidth / 2 + beforeWidth / 2} y={-314} opacity={0.001}>
        <Txt
          text={'the rain'}
          fill={IVORY}
          fontFamily={FONT}
          fontWeight={700}
          fontSize={52}
          letterSpacing={1}
          shadowColor={'rgba(5,14,23,0.65)'}
          shadowBlur={8}
          shadowOffset={[0, 2]}
        />
      </Node>
      <Node
        ref={never}
        x={-firstWidth / 2 + beforeWidth + firstGap + neverWidth / 2}
        y={-314}
        opacity={0.001}
      >
        <Txt
          ref={neverWord}
          text={'never'}
          fill={GOLD}
          fontFamily={FONT}
          fontWeight={700}
          fontSize={52}
          letterSpacing={1}
          shadowColor={'rgba(5,14,23,0.65)'}
          shadowBlur={8}
          shadowOffset={[0, 2]}
        />
      </Node>
      <Node
        ref={bothered}
        x={-secondWidth / 2 + botheredWidth / 2}
        y={-256}
        opacity={0.001}
      >
        <Txt
          text={'bothered'}
          fill={IVORY}
          fontFamily={FONT}
          fontWeight={700}
          fontSize={43}
          letterSpacing={0.7}
          shadowColor={'rgba(5,14,23,0.65)'}
          shadowBlur={7}
          shadowOffset={[0, 2]}
        />
      </Node>
      <Node
        ref={rest}
        x={-secondWidth / 2 + botheredWidth + secondGap + restWidth / 2}
        y={-256}
        opacity={0.001}
      >
        <Txt
          text={'me anyway.'}
          fill={IVORY}
          fontFamily={FONT}
          fontWeight={700}
          fontSize={43}
          letterSpacing={0.7}
          shadowColor={'rgba(5,14,23,0.65)'}
          shadowBlur={7}
          shadowOffset={[0, 2]}
        />
      </Node>
      <Img
        ref={brandShield}
        src={shieldLogo}
        height={118}
        x={0}
        y={298}
        opacity={0}
        scale={0.88}
      />
    </>,
  );

  const updateIcons = (time: number) => {
    for (const icon of icons) {
      const drift = icon.speed * time;
      icon.ref().position([
        positiveModulo(icon.x - drift * 0.62 + 258, WIDTH + 516) - 258,
        positiveModulo(icon.y + drift * 0.78 + 458, HEIGHT + 916) - 458,
      ]);
      icon.ref().rotation(
        icon.rotation + Math.sin(time * 0.48 + icon.phase) * 1.8,
      );
    }
  };
  updateIcons(0);
  yield (function* (): ThreadGenerator {
    while (true) {
      updateIcons(useTime());
      yield;
    }
  })();

  yield* waitFor(3);
  yield* all(
    before().opacity(1, 0.25, easeOutCubic),
    before().y(-320, 0.34, easeOutCubic),
  );
  yield* waitFor(0.2);
  yield* all(
    never().opacity(1, 0.25, easeOutCubic),
    never().y(-320, 0.34, easeOutCubic),
  );
  yield* neverWord().scale(1.09, 0.14, easeOutCubic);
  yield* neverWord().scale(1, 0.2, easeInOutCubic);
  yield* waitFor(0.14);
  yield* all(
    bothered().opacity(1, 0.28, easeOutCubic),
    bothered().y(-262, 0.34, easeOutCubic),
  );
  yield* waitFor(0.18);
  yield* all(
    rest().opacity(1, 0.28, easeOutCubic),
    rest().y(-262, 0.34, easeOutCubic),
  );
  yield* waitFor(0.3);
  yield* all(
    brandShield().opacity(1, 0.7, easeOutCubic),
    brandShield().scale(1, 0.7, easeOutCubic),
  );
  yield* waitFor(Math.max(0, DURATION - useTime()));
});

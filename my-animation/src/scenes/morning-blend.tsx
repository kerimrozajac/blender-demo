import {Circle, Line, Node, Rect, Txt, makeScene2D} from '@motion-canvas/2d';
import {
  all,
  createRef,
  easeInOutCubic,
  easeOutCubic,
  ThreadGenerator,
  useTime,
  waitFor,
} from '@motion-canvas/core';
import '@fontsource/caveat/600.css';

const DURATION = 8;
const CREAM = '#FFF0D5';
const CARAMEL = '#C58B58';
const COFFEE = '#6F432E';

type AccentLine = {
  ref: ReturnType<typeof createRef<Line>>;
  points: [number, number][];
  color: string;
  width: number;
};

export default makeScene2D(function* (view): ThreadGenerator {
  yield document.fonts.load('600 62px Caveat', 'Morning Blend');

  const accents: AccentLine[] = [
    {
      ref: createRef<Line>(),
      points: [[-179, -62], [-169, -69], [-158, -68], [-150, -61]],
      color: CARAMEL,
      width: 2.3,
    },
    {
      ref: createRef<Line>(),
      points: [[159, -93], [165, -103], [176, -107]],
      color: CREAM,
      width: 2,
    },
    {
      ref: createRef<Line>(),
      points: [[-166, 91], [-157, 99], [-147, 98], [-141, 91]],
      color: CREAM,
      width: 2,
    },
    {
      ref: createRef<Line>(),
      points: [[167, 53], [173, 61], [180, 60]],
      color: CARAMEL,
      width: 1.8,
    },
    {
      ref: createRef<Line>(),
      points: [[-157, -143], [-151, -151], [-145, -143], [-151, -135], [-157, -143]],
      color: CREAM,
      width: 1.8,
    },
    {
      ref: createRef<Line>(),
      points: [[160, -146], [166, -154], [172, -146], [166, -138], [160, -146]],
      color: CARAMEL,
      width: 1.7,
    },
  ];
  const glints = [
    createRef<Circle>(),
    createRef<Circle>(),
    createRef<Circle>(),
  ];
  const captionMask = createRef<Rect>();
  const caption = createRef<Node>();

  view.add(
    <>
      {accents.map(({ref, points, color, width}) => (
        <Line
          ref={ref}
          points={points}
          stroke={color}
          lineWidth={width}
          lineCap={'round'}
          lineJoin={'round'}
          end={0}
          opacity={0}
        />
      ))}

      <Circle ref={glints[0]} x={-183} y={-121} width={4} height={4} fill={CREAM} opacity={0} />
      <Circle ref={glints[1]} x={181} y={-9} width={4} height={4} fill={CARAMEL} opacity={0} />
      <Circle ref={glints[2]} x={-171} y={46} width={3} height={3} fill={CREAM} opacity={0} />

      <Node ref={caption} opacity={0.001} cache>
        <Txt
          text={'Morning Blend'}
          x={0}
          y={-258}
          fill={CREAM}
          fontFamily={'Caveat'}
          fontWeight={600}
          fontSize={62}
          letterSpacing={0.1}
          shadowColor={'#2C1A13'}
          shadowBlur={7}
          shadowOffset={[0, 3]}
        />
        <Rect
          ref={captionMask}
          x={-222}
          y={-258}
          offset={[-1, 0]}
          width={0}
          height={90}
          fill={'#FFFFFF'}
          compositeOperation={'destination-in'}
        />
      </Node>
    </>,
  );

  yield* waitFor(Math.max(0, 3.0 - useTime()));
  yield* all(
    ...accents.map(({ref}, index) =>
      ref().end(1, 0.54 + (index % 3) * 0.07, easeOutCubic),
    ),
    ...accents.map(({ref}) => ref().opacity(0.9, 0.32, easeOutCubic)),
    ...glints.map((ref, index) =>
      ref().opacity(0.78, 0.3 + index * 0.06, easeOutCubic),
    ),
  );
  yield* waitFor(Math.max(0, 4.5 - useTime()));
  caption().opacity(1);

  function* floatAccents(): ThreadGenerator {
    while (useTime() < DURATION) {
      const time = useTime();
      accents[0].ref().y(-64 + Math.sin(time * 1.1) * 3.5);
      accents[1].ref().y(-98 + Math.sin(time * 0.9 + 1) * 4);
      accents[2].ref().y(94 + Math.sin(time * 1.0 + 2) * 3);
      accents[3].ref().y(57 + Math.sin(time * 1.2 + 2.5) * 3);
      accents[4].ref().y(-143 + Math.sin(time * 1.1 + 3) * 3);
      accents[5].ref().y(-146 + Math.sin(time * 0.85 + 4) * 3);
      glints[0]().y(-121 + Math.sin(time * 1.3) * 4);
      glints[1]().y(-9 + Math.sin(time * 1.0 + 1) * 4);
      glints[2]().y(46 + Math.sin(time * 1.15 + 2) * 3);
      yield;
    }
  }

  yield* all(
    captionMask().width(444, 1.5, easeInOutCubic),
    floatAccents(),
  );
  yield* waitFor(Math.max(0, DURATION - useTime()));
});

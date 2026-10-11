import {Gradient, Line, Node, Rect, Txt, makeScene2D} from '@motion-canvas/2d';
import {
  Color,
  ThreadGenerator,
  createRef,
  easeInOutCubic,
  easeOutCubic,
  waitFor,
  useTime,
  all,
  tween,
  map,
} from '@motion-canvas/core';
import '@fontsource/poppins/800.css';

const DURATION = 5;
const FPS = 24;

const W = 480;
const H = 640;
const CYAN = '#00F5FF';
const FONT = {
  fontFamily: 'Poppins',
  fontWeight: 800,
  fontSize: 70,
  letterSpacing: 1,
};

function rng(seed: number) {
  return () => {
    seed |= 0;
    seed = (seed + 0x6d2b79f5) | 0;
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const PALETTE = [
  {fill: ['rgba(0,229,255,0.45)', 'rgba(120,255,255,0.18)'], stroke: '#FF4FA3'},
  {fill: ['rgba(255,111,127,0.5)', 'rgba(255,170,150,0.2)'], stroke: '#00D8FF'},
  {fill: ['rgba(190,160,255,0.5)', 'rgba(220,200,255,0.2)'], stroke: '#FFE96B'},
  {fill: ['rgba(255,244,150,0.5)', 'rgba(255,250,200,0.2)'], stroke: '#9B6BFF'},
];

interface BubbleState {
  node: Node;
  s0: number;
  u: number;
  speed: number;
  baseRot: number;
  rotAmp: number;
  rotFreq: number;
  scale: number;
  scaleAmp: number;
  phase: number;
}

const DIR = [Math.SQRT1_2, -Math.SQRT1_2];
const NRM = [Math.SQRT1_2, Math.SQRT1_2];
const PERIOD = 1300;

export default makeScene2D(function* (view) {
  const word = createRef<Node>();
  const sweep = createRef<Rect>();
  const shadowTxt = createRef<Txt>();

  const rand = rng(7);
  const bubbles: BubbleState[] = [];
  const bubbleLayer = (<Node />) as Node;

  const COUNT = 26;
  for (let i = 0; i < COUNT; i++) {
    const pal = PALETTE[i % 4];
    const w = 56 + rand() * 90;
    const h = w * (0.65 + rand() * 0.15);
    const tailX = (rand() < 0.5 ? -1 : 1) * w * 0.25;
    const tl = h * 0.42;
    const hw = w / 2;
    const hh = h / 2;
    const flip = rand() < 0.5 ? -1 : 1;
    const points: [number, number][] = [
      [-hw, -hh],
      [hw, -hh],
      [hw, hh],
      [tailX + 16 * flip, hh],
      [tailX - 14 * flip, hh + tl],
      [tailX - 6 * flip, hh],
      [-hw, hh],
    ];
    const useGradient = i % 3 !== 1;
    const node = (
      <Node opacity={0.9}>
        <Line
          points={points}
          closed
          radius={Math.min(hw, hh) * 0.28}
          fill={
            useGradient
              ? new Gradient({
                  type: 'linear',
                  from: [-hw, -hh],
                  to: [hw, hh],
                  stops: [
                    {offset: 0, color: pal.fill[0]},
                    {offset: 1, color: pal.fill[1]},
                  ],
                })
              : pal.fill[0]
          }
          stroke={pal.stroke}
          lineWidth={1.6}
          lineJoin={'round'}
        />
      </Node>
    ) as Node;
    bubbleLayer.add(node);
    bubbles.push({
      node,
      s0: (rand() - 0.5) * PERIOD,
      u: (rand() - 0.5) * 760,
      speed: 25 + rand() * 90,
      baseRot: (rand() - 0.5) * 30,
      rotAmp: 3 + rand() * 8,
      rotFreq: 0.4 + rand() * 0.8,
      scale: 0.8 + rand() * 0.4,
      scaleAmp: 0.04 + rand() * 0.08,
      phase: rand() * Math.PI * 2,
    });
  }

  const update = (t: number) => {
    for (const b of bubbles) {
      let s = (b.s0 + b.speed * t) % PERIOD;
      if (s > PERIOD / 2) s -= PERIOD;
      b.node.position([DIR[0] * s + NRM[0] * b.u, DIR[1] * s + NRM[1] * b.u]);
      b.node.rotation(b.baseRot + Math.sin(t * b.rotFreq * 2 + b.phase) * b.rotAmp);
      b.node.scale(b.scale * (1 + Math.sin(t * b.rotFreq * 1.7 + b.phase) * b.scaleAmp));
    }
  };
  update(0);

  const glossGradient = new Gradient({
    type: 'linear',
    from: [0, -50],
    to: [0, 50],
    stops: [
      {offset: 0, color: '#FFFFFF'},
      {offset: 0.5, color: '#F2FBFF'},
      {offset: 0.52, color: '#D6EEF7'},
      {offset: 1, color: '#FFFFFF'},
    ],
  });

  view.add(
    <>
      {bubbleLayer}
      <Node ref={word} scale={0.3} opacity={0.001}>
        <Txt
          ref={shadowTxt}
          text={'REPRESENT'}
          fill={glossGradient}
          shadowColor={'rgba(255,60,200,0.55)'}
          shadowBlur={14}
          shadowOffset={[0, 6]}
          {...FONT}
        />
        <Node cache>
          <Txt text={'REPRESENT'} fill={CYAN} {...FONT} />
          <Rect
            ref={sweep}
            x={-330}
            width={150}
            height={140}
            skew={[-12, 0]}
            fill={
              new Gradient({
                type: 'linear',
                from: [-75, 0],
                to: [75, 0],
                stops: [
                  {offset: 0, color: 'rgba(255,255,255,0)'},
                  {offset: 0.5, color: 'rgba(255,255,255,1)'},
                  {offset: 1, color: 'rgba(255,255,255,0)'},
                ],
              })
            }
            compositeOperation={'destination-in'}
          />
        </Node>
      </Node>
    </>,
  );

  // Drive bubbles every frame.
  yield (function* (): ThreadGenerator {
    while (true) {
      update(useTime());
      yield;
    }
  })();

  yield* waitFor(1);
  word().opacity(1);
  yield* word().scale(1.15, 0.14, easeOutCubic);
  yield* word().scale(1, 0.1, easeInOutCubic);
  yield* waitFor(0.25);

  yield* sweep().x(330, 0.9, easeInOutCubic);
  yield* all(
    tween(0.5, (v) => {
      const p = Math.sin(v * Math.PI);
      shadowTxt().shadowBlur(14 + 40 * p);
      shadowTxt().shadowColor(Color.lerp('rgba(255,60,200,0.55)', 'rgba(0,245,255,0.95)', p));
    }),
    word().scale(1.04, 0.25, easeOutCubic).back(0.25),
  );

  yield* waitFor(Math.max(0, DURATION - useTime()));
});

import {
  Img,
  Line,
  Node,
  Txt,
  makeScene2D,
} from '@motion-canvas/2d';
import {
  all,
  createRef,
  easeInOutCubic,
  easeOutCubic,
  makeRef,
  ThreadGenerator,
  useTime,
  waitFor,
} from '@motion-canvas/core';
import '@fontsource/rye/400.css';
import burgerImage from '../../../burger.webp';

const W = 480;
const FPS = 24;
const DURATION = 6;
const POPS = [1.45, 3.25, 5.05];
const INK = '#160806';
const RED = '#650D16';

type Ray = {
  x: number;
  y: number;
  angle: number;
  length: number;
  width: number;
};

const rays: Ray[] = [
  {x: -183, y: -144, angle: 205, length: 26, width: 5},
  {x: -185, y: -119, angle: 180, length: 34, width: 6},
  {x: -176, y: -96, angle: 155, length: 24, width: 4},
  {x: 183, y: -144, angle: -25, length: 26, width: 5},
  {x: 185, y: -119, angle: 0, length: 34, width: 6},
  {x: 176, y: -96, angle: 25, length: 24, width: 4},
];

function taperedRay({x, y, angle, length, width}: Ray) {
  const radians = (angle * Math.PI) / 180;
  const dx = Math.cos(radians);
  const dy = Math.sin(radians);
  const px = -dy * (width / 2);
  const py = dx * (width / 2);
  const tipX = x + dx * length;
  const tipY = y + dy * length;
  const neckX = tipX - dx * 6;
  const neckY = tipY - dy * 6;

  return (
    <Line
      points={[
        [x + px, y + py],
        [neckX + px * 0.16, neckY + py * 0.16],
        [tipX, tipY],
        [neckX - px * 0.16, neckY - py * 0.16],
        [x - px, y - py],
      ]}
      closed
      fill={INK}
    />
  );
}

function popScale(time: number, start: number) {
  const t = (time - start) / 0.42;
  if (t < 0 || t >= 1) return 0;
  if (t < 0.22) return 0.13 * easeOutCubic(t / 0.22);
  if (t < 0.58) return 0.13 - 0.148 * easeOutCubic((t - 0.22) / 0.36);
  return -0.018 * (1 - easeInOutCubic((t - 0.58) / 0.42));
}

function burstState(time: number, start: number) {
  const t = (time - start) / 0.42;
  if (t < 0 || t >= 1) return {opacity: 0, scale: 0.72};
  const opacity = t < 0.16 ? easeOutCubic(t / 0.16) : 1 - easeInOutCubic((t - 0.16) / 0.84);
  return {opacity, scale: 0.72 + 0.48 * easeOutCubic(t)};
}

export default makeScene2D(function* (view) {
  yield document.fonts.load('400 48px Rye');

  const burger = createRef<Node>();
  const burstNodes: Node[] = [];
  const titleA = createRef<Txt>();
  const titleB = createRef<Txt>();
  const borderArtwork = createRef<Node>();
  const topDrips = createRef<Node>();
  const sideDrips = createRef<Node>();

  view.add(
    <>
      <Node ref={burger}>
        <Img src={burgerImage} width={W} height={W * 1.5} />
      </Node>

      <Node ref={borderArtwork} opacity={0.15}>
        <Line
          points={[
            [-240, -320], [240, -320], [240, -274], [220, -281], [197, -263],
            [174, -277], [148, -267], [121, -285], [94, -271], [66, -280],
            [39, -264], [10, -281], [-18, -269], [-47, -285], [-76, -271],
            [-104, -280], [-133, -263], [-162, -278], [-190, -267], [-216, -285],
            [-240, -276],
          ]}
          closed fill={INK} radius={6}
        />
        <Line
          points={[
            [-240, 320], [240, 320], [240, 278], [219, 286], [196, 268],
            [172, 282], [146, 270], [119, 289], [91, 273], [63, 284],
            [35, 269], [7, 286], [-21, 272], [-49, 288], [-77, 272],
            [-105, 283], [-133, 268], [-161, 286], [-189, 271], [-216, 287],
            [-240, 281],
          ]}
          closed fill={INK} radius={6}
        />
        <Line
          points={[
            [-240, -320], [-207, -320], [-220, -274], [-204, -230],
            [-231, -182], [-211, -135], [-232, -83], [-209, -34],
            [-234, 17], [-211, 69], [-232, 121], [-207, 172],
            [-228, 223], [-207, 277], [-216, 320], [-240, 320],
          ]}
          closed fill={INK} radius={6}
        />
        <Line
          points={[
            [240, -320], [207, -320], [218, -277], [203, -233],
            [231, -186], [211, -139], [233, -89], [210, -43],
            [235, 8], [212, 60], [232, 112], [208, 163],
            [229, 217], [207, 276], [217, 320], [240, 320],
          ]}
          closed fill={INK} radius={6}
        />

        <Node ref={topDrips}>
          <Line points={[[-112, -284], [-96, -277], [-102, -258], [-111, -251], [-119, -264]]} closed fill={INK} />
          <Line points={[[52, -279], [66, -284], [70, -261], [62, -251], [54, -262]]} closed fill={INK} />
          <Line points={[[160, -282], [174, -276], [171, -259], [162, -253], [155, -266]]} closed fill={INK} />
        </Node>
        <Node ref={sideDrips}>
          <Line points={[[-218, -42], [-207, -33], [-204, -8], [-212, 2], [-220, -14]]} closed fill={INK} />
          <Line points={[[218, 54], [207, 46], [204, 22], [212, 13], [221, 30]]} closed fill={INK} />
        </Node>

        <Line
          points={[
            [-235, -286], [-213, -290], [-193, -281], [-174, -286],
            [-154, -279], [-134, -286], [-113, -277], [-92, -285],
            [-70, -279], [-48, -286], [-27, -278], [-5, -286],
            [18, -279], [40, -287], [62, -278], [84, -285],
            [106, -277], [128, -286], [149, -279], [171, -287],
            [192, -278], [214, -288], [235, -285],
          ]}
          closed fill={RED} opacity={0.72} radius={3}
        />
        <Line
          points={[
            [-235, 284], [-213, 286], [-192, 277], [-171, 284],
            [-149, 276], [-127, 285], [-105, 277], [-83, 286],
            [-61, 276], [-39, 284], [-17, 276], [5, 286],
            [27, 277], [49, 285], [72, 276], [94, 286],
            [116, 276], [139, 285], [161, 277], [183, 286],
            [205, 276], [224, 285], [235, 283],
          ]}
          closed fill={RED} opacity={0.58} radius={3}
        />
      </Node>

      {POPS.map((_, i) => (
        <Node ref={makeRef(burstNodes, i)} opacity={0} scale={0.72}>
          {rays.map(taperedRay)}
        </Node>
      ))}

      <Txt
        ref={titleA}
        text="BOMBASTIC"
        y={-224}
        x={-300}
        opacity={0}
        fill="rgba(101, 13, 22, 0.85)"
        stroke={INK}
        lineWidth={0.8}
        shadowColor="rgba(22, 8, 6, 0.72)"
        shadowBlur={4}
        shadowOffset={[2, 3]}
        fontFamily="Rye"
        fontSize={48}
        letterSpacing={-0.4}
      />
      <Txt
        ref={titleB}
        text="BURGER"
        y={-174}
        x={300}
        opacity={0}
        fill="rgba(101, 13, 22, 0.85)"
        stroke={INK}
        lineWidth={0.8}
        shadowColor="rgba(22, 8, 6, 0.72)"
        shadowBlur={4}
        shadowOffset={[2, 3]}
        fontFamily="Rye"
        fontSize={58}
        letterSpacing={-0.2}
      />
    </>,
  );

  const titleWidthScale = (title: Txt) => Math.min(1, 444 / title.width());
  titleA().scale(titleWidthScale(titleA()));
  titleB().scale(titleWidthScale(titleB()));

  const update = (time: number) => {
    const pop = POPS.reduce((sum, start) => sum + popScale(time, start), 0);
    burger().scale(1 + pop);

    POPS.forEach((start, i) => {
      const {opacity, scale} = burstState(time, start);
      burstNodes[i].opacity(opacity);
      burstNodes[i].scale(scale);
    });

    topDrips().y(-1.5 + Math.sin(time * 1.35) * 1.5);
    topDrips().rotation(Math.sin(time * 1.1) * 0.8);
    sideDrips().rotation(Math.sin(time * 0.9 + 0.7) * 0.65);
    sideDrips().x(Math.sin(time * 1.2) * 1.2);

    const orbit = (time * Math.PI) / 3;
    borderArtwork().position([Math.cos(orbit) * 2.5, Math.sin(orbit) * 2.5]);
    borderArtwork().rotation(Math.sin(orbit) * 1.5);
  };

  yield* all(
    (function* (): ThreadGenerator {
      yield* waitFor(0.15);
      yield* all(
        titleA().x(9, 0.48, easeOutCubic),
        titleA().opacity(1, 0.24),
      );
      yield* titleA().x(0, 0.12, easeInOutCubic);
    })(),
    (function* (): ThreadGenerator {
      yield* waitFor(0.65);
      yield* all(
        titleB().x(-9, 0.48, easeOutCubic),
        titleB().opacity(1, 0.24),
      );
      yield* titleB().x(0, 0.12, easeInOutCubic);
    })(),
    (function* (): ThreadGenerator {
      while (useTime() < DURATION - 1 / FPS) {
        update(useTime());
        yield;
      }
      update(DURATION - 1 / FPS);
    })(),
    (function* (): ThreadGenerator {
      for (const start of POPS) {
        yield* waitFor(start - useTime());
        yield* waitFor(0.42);
      }
      yield* waitFor(Math.max(0, DURATION - 1 / FPS - useTime()));
    })(),
  );
});

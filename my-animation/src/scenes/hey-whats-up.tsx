import {Circle, Line, Node, Txt, makeScene2D} from '@motion-canvas/2d';
import {
  createRef,
  makeRef,
  useTime,
  waitFor,
} from '@motion-canvas/core';
import '@fontsource/bungee/400.css';
import '@fontsource/fredoka/700.css';

const FPS = 24;
const DURATION = 8;

const CORAL = '#FF7866';
const PALE_YELLOW = '#FFE7A3';
const MINT = '#8BE0C1';
const TEAL_SHADOW = 'rgba(18, 62, 70, 0.62)';

type Bubble = {
  x: number;
  y: number;
  width: number;
  height: number;
  color: string;
  phase: number;
};

type Ray = {
  x: number;
  y: number;
  angle: number;
  length: number;
  width: number;
  color: string;
  phase: number;
};

const bubbles: Bubble[] = [
  {x: -313, y: -228, width: 72, height: 45, color: CORAL, phase: 0.2},
  {x: -250, y: -239, width: 34, height: 28, color: PALE_YELLOW, phase: 1.4},
  {x: -174, y: -232, width: 49, height: 34, color: MINT, phase: 2.6},
  {x: -80, y: -240, width: 29, height: 24, color: CORAL, phase: 4.1},
  {x: 37, y: -238, width: 42, height: 30, color: PALE_YELLOW, phase: 3.3},
  {x: 147, y: -235, width: 35, height: 26, color: MINT, phase: 0.8},
  {x: 244, y: -238, width: 56, height: 35, color: CORAL, phase: 2.2},
  {x: 315, y: -220, width: 66, height: 52, color: PALE_YELLOW, phase: 5.1},
  {x: -316, y: -139, width: 35, height: 48, color: MINT, phase: 3.8},
  {x: 315, y: -118, width: 43, height: 61, color: CORAL, phase: 1.7},
  {x: -317, y: -31, width: 63, height: 42, color: PALE_YELLOW, phase: 5.4},
  {x: 314, y: 8, width: 56, height: 42, color: MINT, phase: 3.1},
  {x: -315, y: 91, width: 48, height: 61, color: CORAL, phase: 2.3},
  {x: 318, y: 112, width: 68, height: 47, color: PALE_YELLOW, phase: 0.4},
  {x: -318, y: 203, width: 72, height: 62, color: MINT, phase: 4.6},
  {x: -240, y: 237, width: 41, height: 33, color: CORAL, phase: 1.1},
  {x: -145, y: 238, width: 56, height: 38, color: PALE_YELLOW, phase: 5.8},
  {x: -45, y: 241, width: 37, height: 30, color: MINT, phase: 2.9},
  {x: 68, y: 237, width: 60, height: 42, color: CORAL, phase: 0.6},
  {x: 179, y: 240, width: 35, height: 28, color: PALE_YELLOW, phase: 3.5},
  {x: 281, y: 234, width: 63, height: 45, color: MINT, phase: 1.9},
  {x: 320, y: 194, width: 41, height: 57, color: CORAL, phase: 4.3},
];

const rays: Ray[] = [
  {x: -111, y: -38, angle: 196, length: 31, width: 10, color: PALE_YELLOW, phase: 0.1},
  {x: -126, y: 4, angle: 184, length: 39, width: 11, color: CORAL, phase: 0.7},
  {x: -111, y: 53, angle: 165, length: 28, width: 9, color: PALE_YELLOW, phase: 1.4},
  {x: -82, y: 94, angle: 145, length: 26, width: 8, color: CORAL, phase: 2.1},
  {x: 111, y: -38, angle: -16, length: 31, width: 10, color: CORAL, phase: 0.4},
  {x: 126, y: 4, angle: -2, length: 39, width: 11, color: PALE_YELLOW, phase: 1.1},
  {x: 111, y: 53, angle: 15, length: 28, width: 9, color: CORAL, phase: 1.8},
  {x: 82, y: 94, angle: 35, length: 26, width: 8, color: PALE_YELLOW, phase: 2.5},
  {x: -27, y: -106, angle: 250, length: 22, width: 8, color: CORAL, phase: 0.9},
  {x: 31, y: -105, angle: 286, length: 23, width: 8, color: PALE_YELLOW, phase: 1.7},
];

const waveBursts = [
  0.12, 0.48, 0.84, 1.2, 1.56, 2.18, 2.54, 2.9, 3.26, 3.62,
  4.28, 4.64, 5.0, 5.36, 5.72, 6.08, 7.0,
];

function clamp01(value: number) {
  return Math.max(0, Math.min(1, value));
}

function smooth(value: number) {
  const t = clamp01(value);
  return t * t * (3 - 2 * t);
}

function outBack(value: number) {
  const t = clamp01(value);
  const c1 = 1.70158;
  const c3 = c1 + 1;
  return 1 + c3 * (t - 1) ** 3 + c1 * (t - 1) ** 2;
}

function taperedRay({x, y, angle, length, width, color}: Ray) {
  const radians = (angle * Math.PI) / 180;
  const dx = Math.cos(radians);
  const dy = Math.sin(radians);
  const px = -dy * (width / 2);
  const py = dx * (width / 2);
  const tipX = x + dx * length;
  const tipY = y + dy * length;
  const neckX = tipX - dx * 7;
  const neckY = tipY - dy * 7;

  return (
    <Line
      points={[
        [x + px, y + py],
        [neckX + px * 0.15, neckY + py * 0.15],
        [tipX, tipY],
        [neckX - px * 0.15, neckY - py * 0.15],
        [x - px, y - py],
      ]}
      closed
      fill={color}
    />
  );
}

function pulse(time: number, start: number, duration: number) {
  const progress = (time - start) / duration;
  if (progress < 0 || progress >= 1) return {opacity: 0, scale: 0.66};
  const fadeIn = smooth(progress / 0.14);
  const fadeOut = 1 - smooth((progress - 0.56) / 0.44);
  return {
    opacity: fadeIn * fadeOut,
    scale: 0.66 + 0.53 * outBack(progress),
  };
}

export default makeScene2D(function* (view) {
  yield document.fonts.load('400 84px Bungee');
  yield document.fonts.load('700 64px Fredoka');

  const bubbleNodes: Node[] = [];
  const rayNodes: Node[] = [];
  const hey = createRef<Txt>();
  const exclamationA = createRef<Txt>();
  const exclamationB = createRef<Txt>();
  const whats = createRef<Txt>();
  const up = createRef<Txt>();

  view.add(
    <>
      {bubbles.map((bubble, index) => (
        <Circle
          ref={makeRef(bubbleNodes, index)}
          x={bubble.x}
          y={bubble.y}
          width={bubble.width}
          height={bubble.height}
          fill={bubble.color}
          opacity={0.69}
        />
      ))}

      {rays.map((ray, index) => (
        <Node ref={makeRef(rayNodes, index)} opacity={0} scale={0.66}>
          {taperedRay(ray)}
        </Node>
      ))}

      <Txt
        ref={exclamationA}
        text="!"
        x={133}
        y={-164}
        fontFamily="Fredoka"
        fontWeight={700}
        fontSize={88}
        fill={CORAL}
        opacity={0}
        shadowColor={TEAL_SHADOW}
        shadowBlur={6}
        shadowOffset={[3, 4]}
      />
      <Txt
        ref={exclamationB}
        text="!"
        x={190}
        y={-153}
        rotation={11}
        fontFamily="Fredoka"
        fontWeight={700}
        fontSize={69}
        fill={PALE_YELLOW}
        opacity={0}
        shadowColor={TEAL_SHADOW}
        shadowBlur={6}
        shadowOffset={[3, 4]}
      />

      <Txt
        ref={hey}
        text="HEY!"
        x={-35}
        y={-166}
        fontFamily="Bungee"
        fontWeight={400}
        fontSize={76}
        letterSpacing={1}
        fill={CORAL}
        opacity={0}
        shadowColor={TEAL_SHADOW}
        shadowBlur={7}
        shadowOffset={[3, 4]}
      />
      <Txt
        ref={whats}
        text="WHAT'S"
        y={-165}
        fontFamily="Fredoka"
        fontWeight={700}
        fontSize={60}
        fill={PALE_YELLOW}
        opacity={0}
        shadowColor={TEAL_SHADOW}
        shadowBlur={7}
        shadowOffset={[3, 4]}
      />
      <Txt
        ref={up}
        text="UP?"
        y={-165}
        fontFamily="Fredoka"
        fontWeight={700}
        fontSize={60}
        fill={PALE_YELLOW}
        opacity={0}
        shadowColor={TEAL_SHADOW}
        shadowBlur={7}
        shadowOffset={[3, 4]}
      />
    </>,
  );

  const wordGap = 17;
  const wordsWidth = whats().width() + wordGap + up().width();
  const wordStartX = -wordsWidth / 2;
  const wordRestX = [
    wordStartX + whats().width() / 2,
    wordStartX + whats().width() + wordGap + up().width() / 2,
  ];
  whats().x(wordRestX[0] + 220);
  up().x(wordRestX[1] + 220);

  const update = (time: number) => {
    bubbles.forEach((bubble, index) => {
      const node = bubbleNodes[index];
      const phase = time * 0.85 + bubble.phase;
      node.position([
        bubble.x + Math.sin(phase * 0.72) * 5.5,
        bubble.y + Math.cos(phase) * 4.8,
      ]);
      node.scale(1 + Math.sin(phase * 1.17) * 0.075);
      node.opacity(0.67 + 0.055 * (0.5 + 0.5 * Math.sin(phase * 0.9)));
    });

    const heyPop = clamp01((time - 0.5) / 0.48);
    let heyScale = 0.4 + 0.68 * outBack(heyPop);
    if (heyPop > 0.72) {
      const settle = smooth((heyPop - 0.72) / 0.28);
      heyScale = 1.15 - 0.15 * settle;
    }
    const heyExit = smooth((time - 3.2) / 0.4);
    hey().scale(heyScale * (1 - 0.12 * heyExit));
    hey().y(-166 - heyExit * 42);
    hey().opacity(smooth((time - 0.5) / 0.12) * (1 - heyExit));

    const markExit = smooth((time - 3.2) / 0.4);
    [
      {node: exclamationA(), start: 1.0, x: 133, y: -164},
      {node: exclamationB(), start: 1.4, x: 190, y: -153},
    ].forEach(({node, start, x, y}, index) => {
      const popProgress = clamp01((time - start) / 0.34);
      const scale = outBack(popProgress) * (1 - markExit);
      node.scale(scale);
      node.position([
        x + Math.sin(time * 3.2 + index) * 3,
        y - Math.sin(time * 3.5 + index * 0.7) * 4,
      ]);
      node.rotation((index === 0 ? -4 : 11) + Math.sin(time * 2.5 + index) * 3.5);
      node.opacity(0.82 * smooth((time - start) / 0.08) * (1 - markExit));
    });

    const wordEnterA = outBack((time - 3.6) / 0.48);
    const wordEnterB = outBack((time - 3.72) / 0.48);
    const bounce = time >= 6.8 && time <= 7.2
      ? Math.sin(((time - 6.8) / 0.4) * Math.PI) * 0.1
      : 0;
    const wordOpacity = (start: number) =>
      smooth((time - start) / 0.15) * (1 - smooth((time - 7.28) / 0.32));
    whats().x(wordRestX[0] + 220 * (1 - wordEnterA));
    up().x(wordRestX[1] + 220 * (1 - wordEnterB));
    whats().opacity(wordOpacity(3.6));
    up().opacity(wordOpacity(3.72));
    whats().scale(1 + bounce);
    up().scale(1 + bounce);
    whats().y(-165 - bounce * 15);
    up().y(-165 - bounce * 15);

    const burstEvents = [...waveBursts, 6.98];
    const activeBurst = burstEvents.reduce((best, start) => {
      const current = pulse(time, start, 0.4);
      return current.opacity > best.opacity ? current : best;
    }, {opacity: 0, scale: 0.66});
    rayNodes.forEach((node, index) => {
      const ray = rays[index];
      const phase = (time * 2.4 + ray.phase) % (Math.PI * 2);
      node.opacity(activeBurst.opacity * (0.83 + 0.17 * Math.sin(phase)));
      node.scale(activeBurst.scale);
      node.rotation(Math.sin(phase) * 4);
    });
  };

  while (useTime() < DURATION - 1 / FPS) {
    update(useTime());
    yield;
  }
  update(DURATION - 1 / FPS);
  yield* waitFor(1 / FPS);
});

import {defineConfig} from 'vite';
import motionCanvas from '@motion-canvas/vite-plugin';
import ffmpeg from '@motion-canvas/ffmpeg';

export default defineConfig({
  plugins: [
    motionCanvas({
      project: [
        './src/project.ts',
        './src/beyond.ts',
        './src/flow.ts',
        './src/dream.ts',
        './src/break-the-pattern.ts',
        './src/think-make-move.ts',
        './src/represent-vertical.ts',
        './src/bombastic-burger.ts',
        './src/hey-whats-up.ts',
        './src/morning-blend.ts',
        './src/umbrella-rain.ts',
      ],
      output: './renders',
    }),
    ffmpeg(),
  ],
});

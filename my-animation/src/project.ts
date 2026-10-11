import {makeProject} from '@motion-canvas/core';

import kinetic from './scenes/kinetic?scene';

export default makeProject({
  name: 'kinetic-typography',
  scenes: [kinetic],
});

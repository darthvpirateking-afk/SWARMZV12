// AnimatedCockpit.tsx — Top-level wrapper that composites the animation ecosystem around
// the main Cockpit component. Drop-in replacement import in App.tsx.
import Cockpit from '../components/Cockpit';
import AnimationComposer from './AnimationComposer';
import { useSwarmzAnimState } from './useSwarmzAnimState';

export function AnimatedCockpit() {
  const anim = useSwarmzAnimState();

  return (
    <AnimationComposer anim={anim}>
      <Cockpit />
    </AnimationComposer>
  );
}

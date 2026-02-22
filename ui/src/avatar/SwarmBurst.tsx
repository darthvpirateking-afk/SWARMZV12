// SwarmBurst.tsx — Operator-triggered particle burst effect
// Renders a brief radial burst of particles from the avatar center.
// Purely cosmetic, fully operator-governed, zero autonomy.

import React, { useEffect, useRef } from 'react';
import { motion, AnimatePresence, useAnimation } from 'framer-motion';
import { AvatarRealm, realmGlowColor } from './AvatarState';

interface SwarmBurstProps {
    trigger: number;           // increment this number to fire a burst
    realm?: AvatarRealm;
    particleCount?: number;
}

interface Particle {
    id: number;
    angle: number;
    distance: number;
    size: number;
    duration: number;
    delay: number;
}

function makeParticles(count: number): Particle[] {
    return Array.from({ length: count }, (_, i) => ({
        id: i,
        angle: (360 / count) * i + Math.random() * 20 - 10,
        distance: 40 + Math.random() * 50,
        size: 3 + Math.random() * 4,
        duration: 0.5 + Math.random() * 0.4,
        delay: Math.random() * 0.15,
    }));
}

const SwarmBurst: React.FC<SwarmBurstProps> = ({
    trigger,
    realm = 'core',
    particleCount = 12,
}) => {
    const [active, setActive] = React.useState(false);
    const [particles, setParticles] = React.useState<Particle[]>([]);
    const prevTrigger = useRef(-1);

    useEffect(() => {
        if (trigger !== prevTrigger.current && trigger > 0) {
            prevTrigger.current = trigger;
            setParticles(makeParticles(particleCount));
            setActive(true);
            const t = setTimeout(() => setActive(false), 900);
            return () => clearTimeout(t);
        }
    }, [trigger, particleCount]);

    const rgb = realmGlowColor[realm];

    return (
        <div style={{ position: 'absolute', top: '50%', left: '50%', pointerEvents: 'none', zIndex: 30 }}>
            <AnimatePresence>
                {active && particles.map(p => {
                    const rad = (p.angle * Math.PI) / 180;
                    const tx = Math.cos(rad) * p.distance;
                    const ty = Math.sin(rad) * p.distance;
                    return (
                        <motion.div
                            key={`${trigger}-${p.id}`}
                            initial={{ x: 0, y: 0, opacity: 1, scale: 1 }}
                            animate={{ x: tx, y: ty, opacity: 0, scale: 0.3 }}
                            exit={{}}
                            transition={{ duration: p.duration, delay: p.delay, ease: 'easeOut' }}
                            style={{
                                position: 'absolute',
                                width: p.size,
                                height: p.size,
                                borderRadius: '50%',
                                background: `rgba(${rgb}, 0.9)`,
                                boxShadow: `0 0 6px rgba(${rgb}, 0.7)`,
                                transform: 'translate(-50%, -50%)',
                            }}
                        />
                    );
                })}
            </AnimatePresence>
        </div>
    );
};

export default SwarmBurst;

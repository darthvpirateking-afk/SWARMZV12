import React, { useEffect, useRef } from 'react';
import { motion, useAnimation, useAnimationControls, AnimatePresence } from 'framer-motion';
import { AvatarExpression, AvatarRealm, realmGlowShadow } from './AvatarState';

type AvatarMotionProps = {
    children: React.ReactNode;
    mode?: AvatarExpression;
    realm?: AvatarRealm;
    heartbeat?: boolean;
};

// Drift intensity per expression mode (operator-governed, no autonomy)
const intensityMap: Record<string, number> = {
    focused:    4,
    analytical: 6,
    calm:       3,
    ceremonial: 8,
    creative:   10,
    neutral:    4,
};

// Drift speed (seconds per cycle) per mode
const speedMap: Record<string, number> = {
    focused:    7,
    analytical: 5,
    calm:       10,
    ceremonial: 4,
    creative:   6,
    neutral:    8,
};

const AvatarMotion: React.FC<AvatarMotionProps> = ({
    children,
    mode = 'focused',
    realm = 'core',
    heartbeat = false,
}) => {
    const driftControls = useAnimation();
    const pulseControls = useAnimation();
    const prevMode = useRef(mode);

    // ── Idle drift loop ─────────────────────────────────────────────
    useEffect(() => {
        const intensity = intensityMap[mode] ?? 4;
        const speed    = speedMap[mode] ?? 7;
        driftControls.start({
            y: [0, -intensity, 0, intensity, 0],
            x: [0, intensity / 2, 0, -intensity / 2, 0],
            transition: {
                duration: speed,
                repeat: Infinity,
                ease: 'easeInOut',
            },
        });
    }, [driftControls, mode]);

    // ── Mode-shift pulse ─────────────────────────────────────────────
    useEffect(() => {
        if (prevMode.current !== mode) {
            prevMode.current = mode;
            pulseControls.start({
                scale: [1, 1.06, 0.97, 1.02, 1],
                transition: { duration: 0.65, ease: 'easeOut' },
            });
        }
    }, [pulseControls, mode]);

    // ── Realm transition flash ────────────────────────────────────────
    const realmControls = useAnimationControls();
    const prevRealm = useRef(realm);
    useEffect(() => {
        if (prevRealm.current !== realm) {
            prevRealm.current = realm;
            realmControls.start({
                opacity: [1, 0.5, 1],
                scale:   [1, 1.04, 1],
                transition: { duration: 0.5 },
            });
        }
    }, [realmControls, realm]);

    // ── Heartbeat pulse (optional) ────────────────────────────────────
    const heartControls = useAnimation();
    useEffect(() => {
        if (!heartbeat) return;
        const beat = async () => {
            while (true) {
                await heartControls.start({ scale: 1.04, transition: { duration: 0.12 } });
                await heartControls.start({ scale: 1.00, transition: { duration: 0.18 } });
                await heartControls.start({ scale: 1.02, transition: { duration: 0.10 } });
                await heartControls.start({ scale: 1.00, transition: { duration: 0.60 } });
                await new Promise(r => setTimeout(r, 1400));
            }
        };
        beat();
    }, [heartControls, heartbeat]);

    const glowFilter = `drop-shadow(${realmGlowShadow[realm] ?? 'none'})`;

    return (
        <motion.div animate={heartbeat ? heartControls : undefined} style={{ display: 'inline-block' }}>
            <motion.div animate={pulseControls} style={{ display: 'inline-block' }}>
                <motion.div animate={realmControls} style={{ display: 'inline-block' }}>
                    <motion.div
                        animate={driftControls}
                        whileHover={{ scale: 1.03 }}
                        transition={{ duration: 0.3 }}
                        style={{
                            display: 'inline-block',
                            filter: glowFilter,
                        }}
                    >
                        {children}
                    </motion.div>
                </motion.div>
            </motion.div>
        </motion.div>
    );
};

export default AvatarMotion;


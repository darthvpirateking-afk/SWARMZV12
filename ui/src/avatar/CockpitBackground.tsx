// CockpitBackground.tsx — Animated cockpit background for SWARMZ UI
// Operator-governed ambient motion. Zero autonomy.

import React, { useEffect, useRef } from 'react';
import { motion, useAnimation } from 'framer-motion';
import { AvatarRealm, realmGlowColor } from './AvatarState';

interface CockpitBackgroundProps {
    realm?: AvatarRealm;
    processing?: boolean;
    children?: React.ReactNode;
}

// Scanning grid line — horizontal sweep
const ScanLine: React.FC<{ color: string; delay: number; duration: number }> = ({ color, delay, duration }) => (
    <motion.div
        style={{
            position: 'absolute',
            left: 0,
            right: 0,
            height: '1px',
            background: `linear-gradient(90deg, transparent 0%, rgba(${color}, 0.4) 30%, rgba(${color}, 0.7) 50%, rgba(${color}, 0.4) 70%, transparent 100%)`,
            pointerEvents: 'none',
        }}
        initial={{ top: '0%', opacity: 0 }}
        animate={{ top: ['0%', '100%'], opacity: [0, 1, 1, 0] }}
        transition={{ duration, delay, repeat: Infinity, ease: 'linear' }}
    />
);

// Floating node dot
const NodeDot: React.FC<{ color: string; x: string; y: string; delay: number }> = ({ color, x, y, delay }) => (
    <motion.div
        style={{
            position: 'absolute',
            left: x,
            top: y,
            width: '4px',
            height: '4px',
            borderRadius: '50%',
            background: `rgba(${color}, 0.5)`,
            boxShadow: `0 0 8px rgba(${color}, 0.4)`,
        }}
        animate={{ opacity: [0.2, 0.8, 0.2], scale: [1, 1.4, 1] }}
        transition={{ duration: 3, delay, repeat: Infinity, ease: 'easeInOut' }}
    />
);

// Corner bracket — static decorative corner
const Corner: React.FC<{ color: string; position: 'tl' | 'tr' | 'bl' | 'br' }> = ({ color, position }) => {
    const styles: Record<string, React.CSSProperties> = {
        tl: { top: 8, left: 8, borderTop: `1px solid rgba(${color}, 0.5)`, borderLeft: `1px solid rgba(${color}, 0.5)` },
        tr: { top: 8, right: 8, borderTop: `1px solid rgba(${color}, 0.5)`, borderRight: `1px solid rgba(${color}, 0.5)` },
        bl: { bottom: 8, left: 8, borderBottom: `1px solid rgba(${color}, 0.5)`, borderLeft: `1px solid rgba(${color}, 0.5)` },
        br: { bottom: 8, right: 8, borderBottom: `1px solid rgba(${color}, 0.5)`, borderRight: `1px solid rgba(${color}, 0.5)` },
    };
    return (
        <div style={{
            position: 'absolute',
            width: '18px',
            height: '18px',
            ...styles[position],
        }} />
    );
};

const CockpitBackground: React.FC<CockpitBackgroundProps> = ({
    realm = 'core',
    processing = false,
    children,
}) => {
    const rgb = realmGlowColor[realm];
    const scanDuration = processing ? 2.5 : 5;

    // Node dot positions (static, operator-defined)
    const nodes = [
        { x: '10%', y: '20%', delay: 0 },
        { x: '85%', y: '15%', delay: 1.2 },
        { x: '25%', y: '75%', delay: 0.6 },
        { x: '70%', y: '80%', delay: 1.8 },
        { x: '50%', y: '40%', delay: 0.9 },
        { x: '90%', y: '55%', delay: 2.1 },
        { x: '5%',  y: '60%', delay: 1.5 },
    ];

    return (
        <div style={{
            position: 'relative',
            width: '100%',
            height: '100%',
            background: `
                radial-gradient(ellipse at center top,
                    rgba(${rgb}, 0.06) 0%,
                    transparent 60%),
                linear-gradient(180deg,
                    rgba(5, 5, 10, 0.98) 0%,
                    rgba(8, 8, 18, 0.99) 100%)
            `,
            overflow: 'hidden',
        }}>
            {/* Grid overlay */}
            <div style={{
                position: 'absolute',
                inset: 0,
                backgroundImage: `
                    linear-gradient(rgba(${rgb}, 0.04) 1px, transparent 1px),
                    linear-gradient(90deg, rgba(${rgb}, 0.04) 1px, transparent 1px)
                `,
                backgroundSize: '40px 40px',
                pointerEvents: 'none',
            }} />

            {/* Scan lines */}
            <ScanLine color={rgb} delay={0}            duration={scanDuration} />
            <ScanLine color={rgb} delay={scanDuration / 2} duration={scanDuration} />

            {/* Node dots */}
            {nodes.map((n, i) => (
                <NodeDot key={i} color={rgb} x={n.x} y={n.y} delay={n.delay} />
            ))}

            {/* Corner brackets */}
            <Corner color={rgb} position="tl" />
            <Corner color={rgb} position="tr" />
            <Corner color={rgb} position="bl" />
            <Corner color={rgb} position="br" />

            {/* Bottom status bar glow */}
            <div style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                height: '2px',
                background: `linear-gradient(90deg, transparent, rgba(${rgb}, 0.6), transparent)`,
            }} />

            {/* Content */}
            <div style={{ position: 'relative', zIndex: 1, height: '100%' }}>
                {children}
            </div>
        </div>
    );
};

export default CockpitBackground;

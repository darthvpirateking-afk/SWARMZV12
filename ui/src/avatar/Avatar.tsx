import React, { useState, useEffect } from 'react';
import { AvatarState, defaultAvatarState, realmGlowColor } from './AvatarState';
import AvatarMotion from './AvatarMotion';

interface AvatarProps {
    state?: AvatarState;
}

const Avatar: React.FC<AvatarProps> = ({ state = defaultAvatarState }) => {
    const [glowIntensity, setGlowIntensity] = useState(0.5);
    const [coreEnergy, setCoreEnergy] = useState(0.8);
    const [ringAngle, setRingAngle] = useState(0);

    // Animate glow + core energy
    useEffect(() => {
        const interval = setInterval(() => {
            setGlowIntensity(0.3 + Math.random() * 0.7);
            setCoreEnergy(0.6 + Math.random() * 0.4);
        }, 2000 + Math.random() * 3000);
        return () => clearInterval(interval);
    }, []);

    // Status ring rotation
    useEffect(() => {
        let raf: number;
        const speed = state.status === 'processing' ? 2 : 0.4;
        const tick = () => {
            setRingAngle(a => (a + speed) % 360);
            raf = requestAnimationFrame(tick);
        };
        raf = requestAnimationFrame(tick);
        return () => cancelAnimationFrame(raf);
    }, [state.status]);

    const realm = state.realm ?? 'core';
    const modeColorRGB = realmGlowColor[realm];

    const processingBoost = state.status === 'processing' ? 1.2 : 1;
    const expressionRadius =
        state.expression === 'focused'    ? '42% 42% 62% 38%' :
        state.expression === 'analytical' ? '45% 45% 55% 55%' :
        state.expression === 'ceremonial' ? '48% 48% 58% 42%' :
        '50% 50% 60% 40%';
    const modeScale  = state.mode === 'executing' ? 1.08 : state.mode === 'reporting' ? 1.04 : 1;
    const modeRotate = state.mode === 'reporting' ? 2 : state.mode === 'listening' ? -1 : 0;

    const avatarStyle: React.CSSProperties = {
        position: 'relative',
        width: '120px',
        height: '140px',
        margin: '0 auto',
        borderRadius: expressionRadius,
        background: `radial-gradient(circle at center,
            rgba(30, 30, 30, 0.95) 20%,
            rgba(10, 10, 10, 0.98) 60%,
            rgba(0, 0, 0, 1) 100%)`,
        border: `2px solid rgba(${modeColorRGB}, ${glowIntensity})`,
        boxShadow: `
            0 0 20px rgba(${modeColorRGB}, ${glowIntensity * 0.6}),
            inset 0 0 15px rgba(${modeColorRGB}, ${glowIntensity * 0.4})
        `,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        flexDirection: 'column',
        transform: `scale(${modeScale}) rotate(${modeRotate}deg)`,
        transition: 'all 0.8s ease-in-out',
    };

    const circuitStyle: React.CSSProperties = {
        position: 'absolute',
        width: '100%',
        height: '100%',
        background: `
            linear-gradient(45deg,
                transparent 45%,
                rgba(${modeColorRGB}, ${glowIntensity * 0.3}) 49%,
                rgba(${modeColorRGB}, ${glowIntensity * 0.6}) 51%,
                transparent 55%),
            linear-gradient(-45deg,
                transparent 45%,
                rgba(${modeColorRGB}, ${glowIntensity * 0.2}) 49%,
                rgba(${modeColorRGB}, ${glowIntensity * 0.4}) 51%,
                transparent 55%)
        `,
        borderRadius: expressionRadius,
        animation: `circuit-pulse ${state.status === 'processing' ? 2.5 : 4}s ease-in-out infinite`,
    };

    const coreStyle: React.CSSProperties = {
        width: '24px',
        height: '24px',
        borderRadius: '50%',
        background: `radial-gradient(circle,
            rgba(255, 215, 0, ${coreEnergy}) 20%,
            rgba(255, 165, 0, ${coreEnergy * 0.8}) 50%,
            rgba(255, 100, 0, ${coreEnergy * 0.4}) 80%,
            transparent 100%)`,
        boxShadow: `
            0 0 15px rgba(255, 215, 0, ${coreEnergy * 0.8 * processingBoost}),
            0 0 30px rgba(255, 165, 0, ${coreEnergy * 0.4 * processingBoost})
        `,
        animation: `core-pulse ${state.status === 'processing' ? 1.6 : 3}s ease-in-out infinite`,
        position: 'relative',
        zIndex: 10,
    };

    const crownFragmentBase: React.CSSProperties = {
        position: 'absolute',
        top: '-15px',
        left: '50%',
        transform: 'translateX(-50%)',
        width: '8px',
        height: '8px',
        background: `rgba(${modeColorRGB}, ${glowIntensity * 0.7})`,
        borderRadius: '50%',
        boxShadow: `0 0 10px rgba(${modeColorRGB}, ${glowIntensity})`,
        animation: 'float 6s ease-in-out infinite',
    };

    // Status ring — rotating arc
    const ringSize = 148;
    const ringRadius = ringSize / 2 - 4;
    const ringCircumference = 2 * Math.PI * ringRadius;
    const ringDash = state.status === 'processing'
        ? ringCircumference * 0.55
        : ringCircumference * 0.25;

    return (
        <div style={{ position: 'relative', display: 'inline-block' }}>
            <style>{`
                @keyframes circuit-pulse {
                    0%, 100% { opacity: 0.4; transform: scale(1); }
                    50%       { opacity: 0.8; transform: scale(1.02); }
                }
                @keyframes core-pulse {
                    0%, 100% { transform: scale(1); }
                    50%       { transform: scale(1.1); }
                }
                @keyframes float {
                    0%, 100% { transform: translateX(-50%) translateY(0px); }
                    33%       { transform: translateX(-50%) translateY(-3px); }
                    66%       { transform: translateX(-50%) translateY(3px); }
                }
            `}</style>

            {/* Status ring — SVG orbit arc */}
            <svg
                width={ringSize}
                height={ringSize}
                style={{
                    position: 'absolute',
                    top: '50%',
                    left: '50%',
                    transform: `translate(-50%, -50%) rotate(${ringAngle}deg)`,
                    pointerEvents: 'none',
                    zIndex: 20,
                }}
            >
                <circle
                    cx={ringSize / 2}
                    cy={ringSize / 2}
                    r={ringRadius}
                    fill="none"
                    stroke={`rgba(${modeColorRGB}, 0.7)`}
                    strokeWidth={state.status === 'processing' ? 2.5 : 1.5}
                    strokeDasharray={`${ringDash} ${ringCircumference - ringDash}`}
                    strokeLinecap="round"
                />
            </svg>

            <AvatarMotion
                mode={state.expression ?? 'neutral'}
                realm={realm}
                heartbeat={state.status === 'processing'}
            >
                <div style={avatarStyle}>
                    {/* Circuit patterns */}
                    <div style={circuitStyle} />

                    {/* Crown fragments */}
                    <div style={crownFragmentBase} />
                    <div style={{ ...crownFragmentBase, left: '30%', animationDelay: '2s' }} />
                    <div style={{ ...crownFragmentBase, left: '70%', animationDelay: '4s' }} />

                    {/* Energy core */}
                    <div style={coreStyle} />

                    {/* Status label */}
                    <div style={{
                        position: 'absolute',
                        bottom: '10px',
                        fontSize: '10px',
                        color: `rgba(${modeColorRGB}, ${glowIntensity})`,
                        textShadow: `0 0 5px rgba(${modeColorRGB}, ${glowIntensity})`,
                    }}>
                        {state.mode.toUpperCase()} • {state.status.toUpperCase()}
                    </div>
                </div>
            </AvatarMotion>

            <div style={{
                textAlign: 'center',
                marginTop: '10px',
                fontSize: '12px',
                color: '#ffd700',
            }}>
                {realm.toUpperCase()} • {state.expression ?? 'neutral'}
            </div>
        </div>
    );
};

export default Avatar;

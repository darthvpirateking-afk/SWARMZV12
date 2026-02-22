// MatrixText.tsx — Slow matrix-style typewriter for AI responses
// Characters appear one by one with a brief green flash, like typing on a terminal.

import React, { useState, useEffect, useRef } from 'react';

interface MatrixTextProps {
  text: string;
  /** Milliseconds between each character */
  speed?: number;
  /** Called once the full text has been revealed */
  onComplete?: () => void;
  /** CSS color for the "active cursor" flash */
  cursorColor?: string;
  style?: React.CSSProperties;
}

const MatrixText: React.FC<MatrixTextProps> = ({
  text,
  speed = 28,
  onComplete,
  cursorColor = '#00ff88',
  style,
}) => {
  const [displayed, setDisplayed] = useState('');
  const [cursorVisible, setCursorVisible] = useState(true);
  const idx = useRef(0);
  const done = useRef(false);

  useEffect(() => {
    // Reset on new text
    idx.current = 0;
    done.current = false;
    setDisplayed('');
    setCursorVisible(true);

    const interval = setInterval(() => {
      if (idx.current < text.length) {
        setDisplayed(text.slice(0, idx.current + 1));
        idx.current++;
      } else if (!done.current) {
        done.current = true;
        setCursorVisible(false);
        onComplete?.();
        clearInterval(interval);
      }
    }, speed);

    return () => clearInterval(interval);
  }, [text, speed, onComplete]);

  // Blinking cursor while typing
  useEffect(() => {
    if (done.current) return;
    const blink = setInterval(() => setCursorVisible(v => !v), 420);
    return () => clearInterval(blink);
  }, [text]);

  return (
    <span style={{
      fontFamily: "'Courier New', 'Consolas', monospace",
      lineHeight: 1.5,
      ...style,
    }}>
      {displayed}
      {!done.current && (
        <span style={{
          display: 'inline-block',
          width: '8px',
          height: '1.1em',
          marginLeft: '1px',
          verticalAlign: 'text-bottom',
          background: cursorVisible ? cursorColor : 'transparent',
          boxShadow: cursorVisible ? `0 0 8px ${cursorColor}, 0 0 16px ${cursorColor}55` : 'none',
          transition: 'background 0.1s, box-shadow 0.1s',
        }} />
      )}
    </span>
  );
};

export default MatrixText;

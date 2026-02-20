import React, { useState } from 'react';
import Avatar from './Avatar';
import { defaultAvatarState, AvatarState } from './AvatarState';
import { sendCommand, validateCommand, triggerSwarmOp, displayMissionProgress, surfaceWarnings } from './AvatarActions';

const AvatarPanel: React.FC = () => {
    const [state, setState] = useState<AvatarState>(defaultAvatarState);
    const [log, setLog] = useState<string[]>([]);

    const handleCommand = (cmd: string) => {
        const validation = validateCommand(cmd);
        const execution = sendCommand(cmd);
        setLog([...log, validation, execution]);
    };

    const handleQuickAction = (action: string) => {
        const result = triggerSwarmOp(action);
        setLog([...log, result]);
    };

    return (
        <div className="avatar-panel">
            <Avatar />
            <div>
                <p>Mode: {state.mode}</p>
                <p>Status: {state.status}</p>
                <p>Expression: {state.expression}</p>
            </div>
            <input
                type="text"
                placeholder="Enter command"
                onKeyDown={(e) => {
                    if (e.key === 'Enter') handleCommand(e.currentTarget.value);
                }}
            />
            <div>
                <button onClick={() => handleQuickAction('example-operation')}>Quick Action</button>
            </div>
            <div>
                <h3>Action Log</h3>
                <ul>
                    {log.map((entry, index) => (
                        <li key={index}>{entry}</li>
                    ))}
                </ul>
            </div>
        </div>
    );
};

export default AvatarPanel;
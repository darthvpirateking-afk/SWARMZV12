import { AvatarState } from './AvatarState';

export const sendCommand = (cmd: string): string => {
    console.log(`Command sent: ${cmd}`);
    return `Command '${cmd}' executed.`;
};

export const validateCommand = (cmd: string): string => {
    console.log(`Validating command: ${cmd}`);
    return `Command '${cmd}' validated.`;
};

export const triggerSwarmOp = (op: string): string => {
    console.log(`Swarm operation triggered: ${op}`);
    return `Swarm operation '${op}' initiated.`;
};

export const displayMissionProgress = (progress: string): string => {
    console.log(`Mission progress: ${progress}`);
    return `Mission progress: ${progress}`;
};

export const surfaceWarnings = (warning: string): string => {
    console.log(`Warning surfaced: ${warning}`);
    return `Warning: ${warning}`;
};
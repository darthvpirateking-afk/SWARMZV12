export type AvatarMode = 'idle' | 'listening' | 'executing' | 'reporting';
export type AvatarStatus = 'online' | 'processing' | 'awaiting_input';
export type AvatarExpression = 'neutral' | 'focused' | 'alert';

export interface AvatarState {
    mode: AvatarMode;
    status: AvatarStatus;
    expression?: AvatarExpression;
}

export const defaultAvatarState: AvatarState = {
    mode: 'idle',
    status: 'online',
    expression: 'neutral',
};
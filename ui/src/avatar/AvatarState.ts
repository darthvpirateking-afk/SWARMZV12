export type AvatarMode = 'idle' | 'listening' | 'executing' | 'reporting';
export type AvatarStatus = 'online' | 'processing' | 'awaiting_input';
export type AvatarExpression = 'neutral' | 'focused' | 'analytical' | 'calm' | 'ceremonial' | 'creative';
export type AvatarRealm = 'cosmos' | 'forge' | 'void' | 'core';

export interface AvatarState {
    mode: AvatarMode;
    status: AvatarStatus;
    expression?: AvatarExpression;
    realm?: AvatarRealm;
}

export const defaultAvatarState: AvatarState = {
    mode: 'idle',
    status: 'online',
    expression: 'neutral',
    realm: 'core',
};

export const realmGlowColor: Record<AvatarRealm, string> = {
    cosmos: '120, 180, 255',
    forge:  '255, 140, 80',
    void:   '180, 80, 255',
    core:   '255, 255, 255',
};

export const realmGlowShadow: Record<AvatarRealm, string> = {
    cosmos: '0px 0px 24px rgba(120, 180, 255, 0.65)',
    forge:  '0px 0px 24px rgba(255, 140, 80, 0.65)',
    void:   '0px 0px 24px rgba(180, 80, 255, 0.65)',
    core:   '0px 0px 24px rgba(255, 255, 255, 0.40)',
};
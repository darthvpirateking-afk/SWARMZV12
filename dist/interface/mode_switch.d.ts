/**
 * Mode Switch - Locks Companion or Operator mode
 * Part of Interface Layer
 */
import { InterfaceMode } from '../types';
export interface ModeConfig {
    mode: InterfaceMode;
    locked: boolean;
    auto_execute: boolean;
    require_confirmation: boolean;
}
export declare class ModeSwitch {
    private currentMode;
    private locked;
    private config;
    constructor(initialMode?: InterfaceMode);
    /**
     * Get current mode
     */
    getCurrentMode(): InterfaceMode;
    /**
     * Switch to a different mode
     */
    switchMode(newMode: InterfaceMode): boolean;
    /**
     * Lock current mode
     */
    lockMode(): void;
    /**
     * Unlock mode switching
     */
    unlockMode(): void;
    /**
     * Get current configuration
     */
    getConfig(): ModeConfig;
    /**
     * Check if mode allows auto-execution
     */
    canAutoExecute(): boolean;
    /**
     * Check if confirmation is required
     */
    needsConfirmation(): boolean;
}
//# sourceMappingURL=mode_switch.d.ts.map
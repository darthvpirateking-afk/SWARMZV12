"use strict";
/**
 * Mode Switch - Locks Companion or Operator mode
 * Part of Interface Layer
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ModeSwitch = void 0;
class ModeSwitch {
    constructor(initialMode = 'companion') {
        this.currentMode = 'companion';
        this.locked = false;
        this.currentMode = initialMode;
        this.config = {
            mode: initialMode,
            locked: false,
            auto_execute: false,
            require_confirmation: true
        };
    }
    /**
     * Get current mode
     */
    getCurrentMode() {
        return this.currentMode;
    }
    /**
     * Switch to a different mode
     */
    switchMode(newMode) {
        if (this.locked) {
            console.warn('Mode is locked, cannot switch');
            return false;
        }
        this.currentMode = newMode;
        this.config.mode = newMode;
        // Adjust settings based on mode
        if (newMode === 'operator') {
            this.config.auto_execute = true;
            this.config.require_confirmation = false;
        }
        else {
            this.config.auto_execute = false;
            this.config.require_confirmation = true;
        }
        return true;
    }
    /**
     * Lock current mode
     */
    lockMode() {
        this.locked = true;
        this.config.locked = true;
    }
    /**
     * Unlock mode switching
     */
    unlockMode() {
        this.locked = false;
        this.config.locked = false;
    }
    /**
     * Get current configuration
     */
    getConfig() {
        return { ...this.config };
    }
    /**
     * Check if mode allows auto-execution
     */
    canAutoExecute() {
        return this.config.auto_execute;
    }
    /**
     * Check if confirmation is required
     */
    needsConfirmation() {
        return this.config.require_confirmation;
    }
}
exports.ModeSwitch = ModeSwitch;
//# sourceMappingURL=mode_switch.js.map
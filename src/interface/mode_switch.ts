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

export class ModeSwitch {
  private currentMode: InterfaceMode = 'companion';
  private locked: boolean = false;
  private config: ModeConfig;

  constructor(initialMode: InterfaceMode = 'companion') {
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
  getCurrentMode(): InterfaceMode {
    return this.currentMode;
  }

  /**
   * Switch to a different mode
   */
  switchMode(newMode: InterfaceMode): boolean {
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
    } else {
      this.config.auto_execute = false;
      this.config.require_confirmation = true;
    }
    
    return true;
  }

  /**
   * Lock current mode
   */
  lockMode(): void {
    this.locked = true;
    this.config.locked = true;
  }

  /**
   * Unlock mode switching
   */
  unlockMode(): void {
    this.locked = false;
    this.config.locked = false;
  }

  /**
   * Get current configuration
   */
  getConfig(): ModeConfig {
    return { ...this.config };
  }

  /**
   * Check if mode allows auto-execution
   */
  canAutoExecute(): boolean {
    return this.config.auto_execute;
  }

  /**
   * Check if confirmation is required
   */
  needsConfirmation(): boolean {
    return this.config.require_confirmation;
  }
}

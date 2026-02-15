/**
 * Countdown - Manages execution countdown timers
 * Part of Commit Engine
 */

import { QueuedAction } from './pending_queue';

export interface CountdownState {
  action_id: string;
  remaining_seconds: number;
  started_at: number;
  will_execute_at: number;
  cancelled: boolean;
}

export class Countdown {
  private countdowns: Map<string, CountdownState> = new Map();
  private intervals: Map<string, NodeJS.Timeout> = new Map();

  /**
   * Start countdown for an action
   */
  start(
    action: QueuedAction,
    callback: (action_id: string) => void
  ): CountdownState {
    const countdown_seconds = action.commit_decision.countdown_seconds || 5;
    const state: CountdownState = {
      action_id: action.id,
      remaining_seconds: countdown_seconds,
      started_at: Date.now(),
      will_execute_at: Date.now() + countdown_seconds * 1000,
      cancelled: false
    };
    
    this.countdowns.set(action.id, state);
    
    // Set up interval to update countdown
    const interval = setInterval(() => {
      const current = this.countdowns.get(action.id);
      if (!current || current.cancelled) {
        this.stop(action.id);
        return;
      }
      
      const elapsed_seconds = Math.floor((Date.now() - current.started_at) / 1000);
      current.remaining_seconds = Math.max(0, countdown_seconds - elapsed_seconds);
      
      if (current.remaining_seconds <= 0) {
        this.stop(action.id);
        callback(action.id);
      }
    }, 1000);
    
    this.intervals.set(action.id, interval);
    
    return state;
  }

  /**
   * Stop countdown
   */
  stop(action_id: string): void {
    const interval = this.intervals.get(action_id);
    if (interval) {
      clearInterval(interval);
      this.intervals.delete(action_id);
    }
    this.countdowns.delete(action_id);
  }

  /**
   * Cancel countdown
   */
  cancel(action_id: string): boolean {
    const state = this.countdowns.get(action_id);
    if (state) {
      state.cancelled = true;
      this.stop(action_id);
      return true;
    }
    return false;
  }

  /**
   * Get countdown state
   */
  getState(action_id: string): CountdownState | undefined {
    return this.countdowns.get(action_id);
  }

  /**
   * Get all active countdowns
   */
  getAll(): CountdownState[] {
    return Array.from(this.countdowns.values());
  }

  /**
   * Clean up all countdowns
   */
  cleanup(): void {
    for (const [action_id, _] of this.countdowns) {
      this.stop(action_id);
    }
  }
}

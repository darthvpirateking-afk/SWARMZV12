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
export declare class Countdown {
    private countdowns;
    private intervals;
    /**
     * Start countdown for an action
     */
    start(action: QueuedAction, callback: (action_id: string) => void): CountdownState;
    /**
     * Stop countdown
     */
    stop(action_id: string): void;
    /**
     * Cancel countdown
     */
    cancel(action_id: string): boolean;
    /**
     * Get countdown state
     */
    getState(action_id: string): CountdownState | undefined;
    /**
     * Get all active countdowns
     */
    getAll(): CountdownState[];
    /**
     * Clean up all countdowns
     */
    cleanup(): void;
}
//# sourceMappingURL=countdown.d.ts.map
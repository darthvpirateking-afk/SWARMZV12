/**
 * Pending Queue - Manages pending actions
 * Part of Commit Engine - prevents thinking forever
 */
import { CommitState } from '../types';
import { CommitDecision } from '../cognition/commit_controller';
export interface QueuedAction {
    id: string;
    commit_decision: CommitDecision;
    state: CommitState;
    queued_at: number;
    execute_at?: number;
}
export declare class PendingQueue {
    private queue;
    /**
     * Add action to pending queue
     */
    enqueue(commit: CommitDecision): QueuedAction;
    /**
     * Get actions ready for execution
     */
    getReadyActions(): QueuedAction[];
    /**
     * Get actions waiting for confirmation
     */
    getWaitingActions(): QueuedAction[];
    /**
     * Get blocked actions
     */
    getBlockedActions(): QueuedAction[];
    /**
     * Update action state
     */
    updateState(action_id: string, new_state: CommitState): boolean;
    /**
     * Remove action from queue
     */
    dequeue(action_id: string): QueuedAction | undefined;
    /**
     * Get queue size
     */
    size(): number;
    /**
     * Clear all actions
     */
    clear(): void;
    /**
     * Get all actions
     */
    getAll(): QueuedAction[];
}
//# sourceMappingURL=pending_queue.d.ts.map
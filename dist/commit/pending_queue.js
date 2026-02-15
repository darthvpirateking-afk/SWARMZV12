"use strict";
/**
 * Pending Queue - Manages pending actions
 * Part of Commit Engine - prevents thinking forever
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.PendingQueue = void 0;
class PendingQueue {
    constructor() {
        this.queue = new Map();
    }
    /**
     * Add action to pending queue
     */
    enqueue(commit) {
        const action = {
            id: `action_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            commit_decision: commit,
            state: commit.state,
            queued_at: Date.now(),
            execute_at: commit.auto_execute
                ? Date.now() + (commit.countdown_seconds || 0) * 1000
                : undefined
        };
        this.queue.set(action.id, action);
        return action;
    }
    /**
     * Get actions ready for execution
     */
    getReadyActions() {
        const now = Date.now();
        return Array.from(this.queue.values()).filter(action => action.state === 'ACTION_READY' &&
            action.execute_at !== undefined &&
            action.execute_at <= now);
    }
    /**
     * Get actions waiting for confirmation
     */
    getWaitingActions() {
        return Array.from(this.queue.values()).filter(action => action.state === 'NEEDS_CONFIRM');
    }
    /**
     * Get blocked actions
     */
    getBlockedActions() {
        return Array.from(this.queue.values()).filter(action => action.state === 'BLOCKED');
    }
    /**
     * Update action state
     */
    updateState(action_id, new_state) {
        const action = this.queue.get(action_id);
        if (!action)
            return false;
        action.state = new_state;
        // If now ready and was waiting, set execute time
        if (new_state === 'ACTION_READY' && !action.execute_at) {
            action.execute_at = Date.now();
        }
        return true;
    }
    /**
     * Remove action from queue
     */
    dequeue(action_id) {
        const action = this.queue.get(action_id);
        if (action) {
            this.queue.delete(action_id);
        }
        return action;
    }
    /**
     * Get queue size
     */
    size() {
        return this.queue.size;
    }
    /**
     * Clear all actions
     */
    clear() {
        this.queue.clear();
    }
    /**
     * Get all actions
     */
    getAll() {
        return Array.from(this.queue.values());
    }
}
exports.PendingQueue = PendingQueue;
//# sourceMappingURL=pending_queue.js.map
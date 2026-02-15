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

export class PendingQueue {
  private queue: Map<string, QueuedAction> = new Map();

  /**
   * Add action to pending queue
   */
  enqueue(commit: CommitDecision): QueuedAction {
    const action: QueuedAction = {
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
  getReadyActions(): QueuedAction[] {
    const now = Date.now();
    return Array.from(this.queue.values()).filter(action => 
      action.state === 'ACTION_READY' && 
      action.execute_at !== undefined &&
      action.execute_at <= now
    );
  }

  /**
   * Get actions waiting for confirmation
   */
  getWaitingActions(): QueuedAction[] {
    return Array.from(this.queue.values()).filter(action => 
      action.state === 'NEEDS_CONFIRM'
    );
  }

  /**
   * Get blocked actions
   */
  getBlockedActions(): QueuedAction[] {
    return Array.from(this.queue.values()).filter(action => 
      action.state === 'BLOCKED'
    );
  }

  /**
   * Update action state
   */
  updateState(action_id: string, new_state: CommitState): boolean {
    const action = this.queue.get(action_id);
    if (!action) return false;
    
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
  dequeue(action_id: string): QueuedAction | undefined {
    const action = this.queue.get(action_id);
    if (action) {
      this.queue.delete(action_id);
    }
    return action;
  }

  /**
   * Get queue size
   */
  size(): number {
    return this.queue.size;
  }

  /**
   * Clear all actions
   */
  clear(): void {
    this.queue.clear();
  }

  /**
   * Get all actions
   */
  getAll(): QueuedAction[] {
    return Array.from(this.queue.values());
  }
}

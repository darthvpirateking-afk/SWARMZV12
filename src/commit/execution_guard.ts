/**
 * Execution Guard - Final safety check before execution
 * Part of Commit Engine
 */

import { QueuedAction } from './pending_queue';
import { Action } from '../types';

export interface GuardResult {
  allowed: boolean;
  reason: string;
  warnings: string[];
  require_preview: boolean;
}

export class ExecutionGuard {
  private executionLog: Array<{
    action_id: string;
    timestamp: number;
    allowed: boolean;
  }> = [];

  /**
   * Final check before allowing execution
   */
  check(action: QueuedAction): GuardResult {
    const warnings: string[] = [];
    let allowed = true;
    let reason = 'Execution approved';

    // Check state
    if (action.state !== 'ACTION_READY') {
      allowed = false;
      reason = `Action state is ${action.state}, not ACTION_READY`;
    }

    // Check if action is too old
    const age_ms = Date.now() - action.queued_at;
    const max_age_ms = 300000; // 5 minutes
    if (age_ms > max_age_ms) {
      allowed = false;
      reason = 'Action has been queued too long and may be stale';
    }

    // Check if action was supposed to execute by now
    if (action.execute_at && Date.now() < action.execute_at) {
      allowed = false;
      reason = 'Action execute time has not been reached';
    }

    // Add warnings for high-risk actions
    const task_action = action.commit_decision.task_id.toLowerCase();
    if (task_action.includes('delete') || task_action.includes('remove')) {
      warnings.push('This action is destructive');
    }

    const result: GuardResult = {
      allowed,
      reason,
      warnings,
      require_preview: warnings.length > 0
    };

    // Log the check
    this.executionLog.push({
      action_id: action.id,
      timestamp: Date.now(),
      allowed
    });

    return result;
  }

  /**
   * Verify action can be executed
   */
  async verify(action: Action): Promise<boolean> {
    try {
      // Generate preview to ensure action is valid
      const preview = await action.preview();
      return preview.length > 0;
    } catch (error) {
      console.error('Action preview failed:', error);
      return false;
    }
  }

  /**
   * Record execution attempt
   */
  recordExecution(action_id: string, success: boolean, error?: string): void {
    this.executionLog.push({
      action_id,
      timestamp: Date.now(),
      allowed: success
    });
  }

  /**
   * Get execution history
   */
  getHistory(limit?: number): Array<any> {
    const history = [...this.executionLog].reverse();
    return limit ? history.slice(0, limit) : history;
  }

  /**
   * Clear execution log
   */
  clearLog(): void {
    this.executionLog = [];
  }

  /**
   * Get statistics
   */
  getStats(): {
    total_checks: number;
    allowed: number;
    blocked: number;
    success_rate: number;
  } {
    const total = this.executionLog.length;
    const allowed = this.executionLog.filter(e => e.allowed).length;
    
    return {
      total_checks: total,
      allowed,
      blocked: total - allowed,
      success_rate: total > 0 ? allowed / total : 0
    };
  }
}

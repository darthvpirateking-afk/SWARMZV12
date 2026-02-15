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
export declare class ExecutionGuard {
    private executionLog;
    /**
     * Final check before allowing execution
     */
    check(action: QueuedAction): GuardResult;
    /**
     * Verify action can be executed
     */
    verify(action: Action): Promise<boolean>;
    /**
     * Record execution attempt
     */
    recordExecution(action_id: string, success: boolean, error?: string): void;
    /**
     * Get execution history
     */
    getHistory(limit?: number): Array<any>;
    /**
     * Clear execution log
     */
    clearLog(): void;
    /**
     * Get statistics
     */
    getStats(): {
        total_checks: number;
        allowed: number;
        blocked: number;
        success_rate: number;
    };
}
//# sourceMappingURL=execution_guard.d.ts.map
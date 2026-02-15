/**
 * Commit Controller - Produces commit state
 * Part of Cognition Core
 */
import { CommitState, TaskPacket } from '../types';
import { RiskAssessment } from './risk_gate';
import { Decision } from './decision_engine';
export interface CommitDecision {
    task_id: string;
    state: CommitState;
    auto_execute: boolean;
    requires_confirmation: boolean;
    countdown_seconds?: number;
    justification: string;
}
export declare class CommitController {
    private default_countdown_seconds;
    /**
     * Determine commit state for a task
     */
    determineCommit(task: TaskPacket, risk: RiskAssessment, decision: Decision): CommitDecision;
    private calculateState;
    private canAutoExecute;
    private generateJustification;
    /**
     * Process user confirmation
     */
    processConfirmation(commit: CommitDecision, confirmed: boolean): CommitDecision;
    /**
     * Update countdown
     */
    updateCountdown(commit: CommitDecision, seconds: number): CommitDecision;
}
//# sourceMappingURL=commit_controller.d.ts.map
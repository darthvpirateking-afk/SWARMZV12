/**
 * Risk Gate - Determines if an action is safe
 * Part of Cognition Core
 */
import { TaskPacket } from '../types';
export interface RiskAssessment {
    task_id: string;
    risk_level: 'low' | 'medium' | 'high' | 'critical';
    can_proceed: boolean;
    warnings: string[];
    required_approvals: string[];
    mitigation_steps: string[];
}
export declare class RiskGate {
    private riskyPatterns;
    /**
     * Assess risk for a task
     */
    assess(task: TaskPacket): RiskAssessment;
    private calculateRiskLevel;
    private identifyWarnings;
    private canProceed;
    private getRequiredApprovals;
    private getMitigationSteps;
    /**
     * Override risk assessment (operator sovereignty)
     */
    override(assessment: RiskAssessment, operator_approval: boolean): RiskAssessment;
}
//# sourceMappingURL=risk_gate.d.ts.map
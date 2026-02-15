/**
 * Decision Engine - Determines best course of action
 * Part of Cognition Core
 */
import { TaskPacket } from '../types';
import { ExecutionPlan } from './planner';
export interface Decision {
    task_id: string;
    should_execute: boolean;
    execution_plan: ExecutionPlan | null;
    rationale: string;
    alternatives: string[];
    confidence: number;
}
export declare class DecisionEngine {
    /**
     * Make a decision about how to handle a task
     */
    decide(task: TaskPacket, plan: ExecutionPlan): Decision;
    private assessConfidence;
    private shouldExecute;
    private generateRationale;
    private findAlternatives;
    /**
     * Re-evaluate a decision based on new information
     */
    reevaluate(decision: Decision, new_info: Record<string, any>): Decision;
}
//# sourceMappingURL=decision_engine.d.ts.map
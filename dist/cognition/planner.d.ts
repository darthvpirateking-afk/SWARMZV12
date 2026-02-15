/**
 * Planner - Chooses best action for a task
 * Part of Cognition Core
 */
import { TaskPacket } from '../types';
export interface ExecutionPlan {
    task_id: string;
    steps: ExecutionStep[];
    estimated_time_ms: number;
    required_workers: string[];
    dependencies: string[];
}
export interface ExecutionStep {
    order: number;
    action: string;
    worker_type: 'scout' | 'builder' | 'verify';
    parameters: Record<string, any>;
    timeout_ms: number;
}
export declare class Planner {
    /**
     * Create an execution plan for a task packet
     */
    plan(task: TaskPacket): ExecutionPlan;
    private determineSteps;
    private estimateTime;
    private identifyWorkers;
    private extractDependencies;
    /**
     * Optimize plan based on constraints
     */
    optimize(plan: ExecutionPlan, constraints: {
        max_time_ms?: number;
    }): ExecutionPlan;
}
//# sourceMappingURL=planner.d.ts.map
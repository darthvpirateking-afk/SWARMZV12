/**
 * Swarm Controller - Spawns controlled workers and collects artifacts
 * Part of Swarm Orchestrator - routes work, never thinks or talks to user
 */
import { TaskPacket, WorkerResult } from '../types';
import { ExecutionPlan } from '../cognition/planner';
export interface WorkerTask {
    id: string;
    worker_type: string;
    plan_step: any;
    task_packet: TaskPacket;
    started_at?: number;
    completed_at?: number;
}
export declare class SwarmController {
    private activeWorkers;
    private completedTasks;
    /**
     * Dispatch workers for an execution plan
     */
    dispatch(plan: ExecutionPlan, task: TaskPacket): Promise<WorkerResult[]>;
    private createWorkerTask;
    private executeWorkerTask;
    private createErrorResult;
    /**
     * Get status of active workers
     */
    getActiveWorkers(): WorkerTask[];
    /**
     * Get completed task results
     */
    getCompletedResults(): WorkerResult[];
    /**
     * Cancel all active workers
     */
    cancelAll(): void;
}
//# sourceMappingURL=swarm_controller.d.ts.map
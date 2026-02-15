"use strict";
/**
 * Swarm Controller - Spawns controlled workers and collects artifacts
 * Part of Swarm Orchestrator - routes work, never thinks or talks to user
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.SwarmController = void 0;
class SwarmController {
    constructor() {
        this.activeWorkers = new Map();
        this.completedTasks = new Map();
    }
    /**
     * Dispatch workers for an execution plan
     */
    async dispatch(plan, task) {
        const results = [];
        for (const step of plan.steps) {
            const workerTask = this.createWorkerTask(step, task);
            this.activeWorkers.set(workerTask.id, workerTask);
            try {
                const result = await this.executeWorkerTask(workerTask, step.timeout_ms);
                results.push(result);
                this.completedTasks.set(workerTask.id, result);
            }
            catch (error) {
                results.push(this.createErrorResult(workerTask, error));
            }
            finally {
                this.activeWorkers.delete(workerTask.id);
            }
        }
        return results;
    }
    createWorkerTask(step, task) {
        return {
            id: `worker_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            worker_type: step.worker_type,
            plan_step: step,
            task_packet: task,
            started_at: Date.now()
        };
    }
    async executeWorkerTask(workerTask, timeout_ms) {
        const startTime = Date.now();
        // This would dispatch to actual worker implementation
        // For now, simulate worker execution
        await new Promise(resolve => setTimeout(resolve, 100));
        const endTime = Date.now();
        return {
            task_id: workerTask.task_packet.id,
            status: 'success',
            data: {
                worker_type: workerTask.worker_type,
                action: workerTask.plan_step.action
            },
            artifacts: [],
            cost: {
                time_ms: endTime - startTime
            }
        };
    }
    createErrorResult(workerTask, error) {
        return {
            task_id: workerTask.task_packet.id,
            status: 'failure',
            data: null,
            artifacts: [],
            cost: {
                time_ms: Date.now() - (workerTask.started_at || Date.now())
            },
            errors: [error.message]
        };
    }
    /**
     * Get status of active workers
     */
    getActiveWorkers() {
        return Array.from(this.activeWorkers.values());
    }
    /**
     * Get completed task results
     */
    getCompletedResults() {
        return Array.from(this.completedTasks.values());
    }
    /**
     * Cancel all active workers
     */
    cancelAll() {
        this.activeWorkers.clear();
    }
}
exports.SwarmController = SwarmController;
//# sourceMappingURL=swarm_controller.js.map
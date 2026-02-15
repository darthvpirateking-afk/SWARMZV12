"use strict";
/**
 * Worker Limits - Enforces worker constraints
 * Part of Swarm Orchestrator
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.WorkerLimitsEnforcer = void 0;
class WorkerLimitsEnforcer {
    constructor(limits) {
        this.currentWorkerCount = 0;
        this.workersByType = new Map();
        this.limits = {
            max_total_workers: limits?.max_total_workers || 10,
            max_per_type: limits?.max_per_type || 5,
            max_execution_time_ms: limits?.max_execution_time_ms || 60000,
            max_memory_mb: limits?.max_memory_mb || 512,
            max_cost_per_task: limits?.max_cost_per_task || 100
        };
    }
    /**
     * Check if can spawn a new worker
     */
    canSpawn(worker_type) {
        // Check total limit
        if (this.currentWorkerCount >= this.limits.max_total_workers) {
            return false;
        }
        // Check per-type limit
        const typeCount = this.workersByType.get(worker_type) || 0;
        if (typeCount >= this.limits.max_per_type) {
            return false;
        }
        return true;
    }
    /**
     * Register a spawned worker
     */
    registerSpawn(worker_type) {
        this.currentWorkerCount++;
        const current = this.workersByType.get(worker_type) || 0;
        this.workersByType.set(worker_type, current + 1);
    }
    /**
     * Unregister a completed worker
     */
    unregisterWorker(worker_type) {
        this.currentWorkerCount = Math.max(0, this.currentWorkerCount - 1);
        const current = this.workersByType.get(worker_type) || 0;
        this.workersByType.set(worker_type, Math.max(0, current - 1));
    }
    /**
     * Check if execution time is within limits
     */
    isWithinTimeLimit(execution_time_ms) {
        return execution_time_ms <= this.limits.max_execution_time_ms;
    }
    /**
     * Check if cost is within limits
     */
    isWithinCostLimit(cost) {
        return cost <= this.limits.max_cost_per_task;
    }
    /**
     * Get current utilization
     */
    getUtilization() {
        return {
            total: this.currentWorkerCount,
            by_type: Object.fromEntries(this.workersByType),
            available: this.limits.max_total_workers - this.currentWorkerCount
        };
    }
    /**
     * Reset all counts
     */
    reset() {
        this.currentWorkerCount = 0;
        this.workersByType.clear();
    }
    /**
     * Update limits
     */
    updateLimits(newLimits) {
        this.limits = { ...this.limits, ...newLimits };
    }
    /**
     * Get current limits
     */
    getLimits() {
        return { ...this.limits };
    }
}
exports.WorkerLimitsEnforcer = WorkerLimitsEnforcer;
//# sourceMappingURL=worker_limits.js.map
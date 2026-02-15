/**
 * Worker Limits - Enforces worker constraints
 * Part of Swarm Orchestrator
 */
export interface WorkerLimits {
    max_total_workers: number;
    max_per_type: number;
    max_execution_time_ms: number;
    max_memory_mb: number;
    max_cost_per_task: number;
}
export declare class WorkerLimitsEnforcer {
    private limits;
    private currentWorkerCount;
    private workersByType;
    constructor(limits?: Partial<WorkerLimits>);
    /**
     * Check if can spawn a new worker
     */
    canSpawn(worker_type: string): boolean;
    /**
     * Register a spawned worker
     */
    registerSpawn(worker_type: string): void;
    /**
     * Unregister a completed worker
     */
    unregisterWorker(worker_type: string): void;
    /**
     * Check if execution time is within limits
     */
    isWithinTimeLimit(execution_time_ms: number): boolean;
    /**
     * Check if cost is within limits
     */
    isWithinCostLimit(cost: number): boolean;
    /**
     * Get current utilization
     */
    getUtilization(): {
        total: number;
        by_type: Record<string, number>;
        available: number;
    };
    /**
     * Reset all counts
     */
    reset(): void;
    /**
     * Update limits
     */
    updateLimits(newLimits: Partial<WorkerLimits>): void;
    /**
     * Get current limits
     */
    getLimits(): WorkerLimits;
}
//# sourceMappingURL=worker_limits.d.ts.map
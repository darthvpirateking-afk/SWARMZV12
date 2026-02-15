/**
 * Worker Registry - Manages available workers
 * Part of Swarm Orchestrator
 */
export interface WorkerMetadata {
    type: string;
    capabilities: string[];
    max_concurrent: number;
    average_time_ms: number;
    success_rate: number;
}
export declare class WorkerRegistry {
    private workers;
    private activeCount;
    constructor();
    /**
     * Register a new worker type
     */
    register(metadata: WorkerMetadata): void;
    /**
     * Get worker metadata
     */
    getWorker(type: string): WorkerMetadata | undefined;
    /**
     * Check if worker is available
     */
    isAvailable(type: string): boolean;
    /**
     * Mark worker as active
     */
    markActive(type: string): boolean;
    /**
     * Mark worker as inactive
     */
    markInactive(type: string): void;
    /**
     * Get all registered workers
     */
    listWorkers(): WorkerMetadata[];
    /**
     * Update worker statistics
     */
    updateStats(type: string, time_ms: number, success: boolean): void;
    private registerDefaultWorkers;
}
//# sourceMappingURL=worker_registry.d.ts.map
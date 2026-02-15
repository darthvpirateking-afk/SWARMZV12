"use strict";
/**
 * Worker Registry - Manages available workers
 * Part of Swarm Orchestrator
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.WorkerRegistry = void 0;
class WorkerRegistry {
    constructor() {
        this.workers = new Map();
        this.activeCount = new Map();
        this.registerDefaultWorkers();
    }
    /**
     * Register a new worker type
     */
    register(metadata) {
        this.workers.set(metadata.type, metadata);
        this.activeCount.set(metadata.type, 0);
    }
    /**
     * Get worker metadata
     */
    getWorker(type) {
        return this.workers.get(type);
    }
    /**
     * Check if worker is available
     */
    isAvailable(type) {
        const worker = this.workers.get(type);
        if (!worker)
            return false;
        const active = this.activeCount.get(type) || 0;
        return active < worker.max_concurrent;
    }
    /**
     * Mark worker as active
     */
    markActive(type) {
        if (!this.isAvailable(type)) {
            return false;
        }
        const current = this.activeCount.get(type) || 0;
        this.activeCount.set(type, current + 1);
        return true;
    }
    /**
     * Mark worker as inactive
     */
    markInactive(type) {
        const current = this.activeCount.get(type) || 0;
        this.activeCount.set(type, Math.max(0, current - 1));
    }
    /**
     * Get all registered workers
     */
    listWorkers() {
        return Array.from(this.workers.values());
    }
    /**
     * Update worker statistics
     */
    updateStats(type, time_ms, success) {
        const worker = this.workers.get(type);
        if (!worker)
            return;
        // Simple running average
        worker.average_time_ms = (worker.average_time_ms + time_ms) / 2;
        // Update success rate
        const currentSuccess = worker.success_rate;
        worker.success_rate = success
            ? (currentSuccess + 1.0) / 2
            : currentSuccess * 0.9;
    }
    registerDefaultWorkers() {
        this.register({
            type: 'scout',
            capabilities: ['read', 'search', 'analyze'],
            max_concurrent: 5,
            average_time_ms: 1000,
            success_rate: 0.95
        });
        this.register({
            type: 'builder',
            capabilities: ['create', 'modify', 'build'],
            max_concurrent: 3,
            average_time_ms: 5000,
            success_rate: 0.85
        });
        this.register({
            type: 'verify',
            capabilities: ['test', 'validate', 'check'],
            max_concurrent: 5,
            average_time_ms: 2000,
            success_rate: 0.90
        });
    }
}
exports.WorkerRegistry = WorkerRegistry;
//# sourceMappingURL=worker_registry.js.map
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

export class WorkerLimitsEnforcer {
  private limits: WorkerLimits;
  private currentWorkerCount: number = 0;
  private workersByType: Map<string, number> = new Map();

  constructor(limits?: Partial<WorkerLimits>) {
    this.limits = {
      max_total_workers: limits?.max_total_workers || 10,
      max_per_type: limits?.max_per_type || 5,
      max_execution_time_ms: limits?.max_execution_time_ms || 60000,
      max_memory_mb: limits?.max_memory_mb || 512,
      max_cost_per_task: limits?.max_cost_per_task || 100,
    };
  }

  /**
   * Check if can spawn a new worker
   */
  canSpawn(worker_type: string): boolean {
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
  registerSpawn(worker_type: string): void {
    this.currentWorkerCount++;
    const current = this.workersByType.get(worker_type) || 0;
    this.workersByType.set(worker_type, current + 1);
  }

  /**
   * Unregister a completed worker
   */
  unregisterWorker(worker_type: string): void {
    this.currentWorkerCount = Math.max(0, this.currentWorkerCount - 1);
    const current = this.workersByType.get(worker_type) || 0;
    this.workersByType.set(worker_type, Math.max(0, current - 1));
  }

  /**
   * Check if execution time is within limits
   */
  isWithinTimeLimit(execution_time_ms: number): boolean {
    return execution_time_ms <= this.limits.max_execution_time_ms;
  }

  /**
   * Check if cost is within limits
   */
  isWithinCostLimit(cost: number): boolean {
    return cost <= this.limits.max_cost_per_task;
  }

  /**
   * Get current utilization
   */
  getUtilization(): {
    total: number;
    by_type: Record<string, number>;
    available: number;
  } {
    return {
      total: this.currentWorkerCount,
      by_type: Object.fromEntries(this.workersByType),
      available: this.limits.max_total_workers - this.currentWorkerCount,
    };
  }

  /**
   * Reset all counts
   */
  reset(): void {
    this.currentWorkerCount = 0;
    this.workersByType.clear();
  }

  /**
   * Update limits
   */
  updateLimits(newLimits: Partial<WorkerLimits>): void {
    this.limits = { ...this.limits, ...newLimits };
  }

  /**
   * Get current limits
   */
  getLimits(): WorkerLimits {
    return { ...this.limits };
  }
}

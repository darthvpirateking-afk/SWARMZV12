/**
 * Weight Adjuster - Adjusts routing weights based on performance
 * Part of Evolution Engine - safe adaptation
 */
export interface RoutingWeight {
    worker_type: string;
    action_type: string;
    weight: number;
    last_updated: number;
    performance_score: number;
}
export declare class WeightAdjuster {
    private weights;
    private learningRate;
    /**
     * Initialize weights for a worker-action pair
     */
    initialize(worker_type: string, action_type: string): RoutingWeight;
    /**
     * Adjust weight based on performance outcome
     */
    adjust(worker_type: string, action_type: string, success: boolean, duration_ms: number, expected_duration_ms: number): RoutingWeight;
    /**
     * Get weight for worker-action pair
     */
    getWeight(worker_type: string, action_type: string): number;
    /**
     * Get all weights
     */
    getAllWeights(): RoutingWeight[];
    /**
     * Get best worker for action type
     */
    getBestWorker(action_type: string): string | null;
    /**
     * Reset all weights
     */
    reset(): void;
    /**
     * Set learning rate
     */
    setLearningRate(rate: number): void;
}
//# sourceMappingURL=weight_adjuster.d.ts.map
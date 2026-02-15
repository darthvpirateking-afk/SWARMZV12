"use strict";
/**
 * Weight Adjuster - Adjusts routing weights based on performance
 * Part of Evolution Engine - safe adaptation
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.WeightAdjuster = void 0;
class WeightAdjuster {
    constructor() {
        this.weights = new Map();
        this.learningRate = 0.1;
    }
    /**
     * Initialize weights for a worker-action pair
     */
    initialize(worker_type, action_type) {
        const key = `${worker_type}:${action_type}`;
        const weight = {
            worker_type,
            action_type,
            weight: 1.0,
            last_updated: Date.now(),
            performance_score: 0.5
        };
        this.weights.set(key, weight);
        return weight;
    }
    /**
     * Adjust weight based on performance outcome
     */
    adjust(worker_type, action_type, success, duration_ms, expected_duration_ms) {
        const key = `${worker_type}:${action_type}`;
        let weight = this.weights.get(key);
        if (!weight) {
            weight = this.initialize(worker_type, action_type);
        }
        // Calculate performance score
        const duration_ratio = duration_ms / expected_duration_ms;
        const time_score = Math.max(0, 1 - (duration_ratio - 1));
        const success_score = success ? 1.0 : 0.0;
        const performance = (time_score + success_score) / 2;
        // Update performance score with exponential moving average
        weight.performance_score =
            (1 - this.learningRate) * weight.performance_score +
                this.learningRate * performance;
        // Adjust weight based on performance score
        weight.weight = 0.5 + weight.performance_score * 1.5; // Range: 0.5 to 2.0
        weight.last_updated = Date.now();
        return weight;
    }
    /**
     * Get weight for worker-action pair
     */
    getWeight(worker_type, action_type) {
        const key = `${worker_type}:${action_type}`;
        const weight = this.weights.get(key);
        return weight ? weight.weight : 1.0;
    }
    /**
     * Get all weights
     */
    getAllWeights() {
        return Array.from(this.weights.values());
    }
    /**
     * Get best worker for action type
     */
    getBestWorker(action_type) {
        const candidates = Array.from(this.weights.values())
            .filter(w => w.action_type === action_type)
            .sort((a, b) => b.weight - a.weight);
        return candidates.length > 0 ? candidates[0].worker_type : null;
    }
    /**
     * Reset all weights
     */
    reset() {
        for (const weight of this.weights.values()) {
            weight.weight = 1.0;
            weight.performance_score = 0.5;
        }
    }
    /**
     * Set learning rate
     */
    setLearningRate(rate) {
        this.learningRate = Math.max(0, Math.min(1, rate));
    }
}
exports.WeightAdjuster = WeightAdjuster;
//# sourceMappingURL=weight_adjuster.js.map
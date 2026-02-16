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

export class WeightAdjuster {
  private weights: Map<string, RoutingWeight> = new Map();
  private learningRate = 0.1;

  /**
   * Initialize weights for a worker-action pair
   */
  initialize(worker_type: string, action_type: string): RoutingWeight {
    const key = `${worker_type}:${action_type}`;
    
    const weight: RoutingWeight = {
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
  adjust(
    worker_type: string,
    action_type: string,
    success: boolean,
    duration_ms: number,
    expected_duration_ms: number
  ): RoutingWeight {
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
  getWeight(worker_type: string, action_type: string): number {
    const key = `${worker_type}:${action_type}`;
    const weight = this.weights.get(key);
    return weight ? weight.weight : 1.0;
  }

  /**
   * Get all weights
   */
  getAllWeights(): RoutingWeight[] {
    return Array.from(this.weights.values());
  }

  /**
   * Get best worker for action type
   */
  getBestWorker(action_type: string): string | null {
    const candidates = Array.from(this.weights.values())
      .filter(w => w.action_type === action_type)
      .sort((a, b) => b.weight - a.weight);
    
    return candidates.length > 0 ? candidates[0].worker_type : null;
  }

  /**
   * Reset all weights
   */
  reset(): void {
    for (const weight of this.weights.values()) {
      weight.weight = 1.0;
      weight.performance_score = 0.5;
    }
  }

  /**
   * Set learning rate
   */
  setLearningRate(rate: number): void {
    this.learningRate = Math.max(0, Math.min(1, rate));
  }
}

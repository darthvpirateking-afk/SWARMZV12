/**
 * Cost Tracker - Tracks resource costs
 * Part of Measurement Spine
 */

export interface CostEntry {
  timestamp: number;
  action: string;
  costs: {
    time_ms: number;
    tokens?: number;
    api_calls?: number;
    memory_mb?: number;
    compute_units?: number;
  };
  estimated_dollar_cost?: number;
}

export class CostTracker {
  private costs: CostEntry[] = [];
  private pricing = {
    token_cost_per_1k: 0.002,
    api_call_cost: 0.001,
    compute_unit_cost: 0.0001,
  };

  /**
   * Track cost for an action
   */
  track(action: string, costs: CostEntry["costs"]): CostEntry {
    const entry: CostEntry = {
      timestamp: Date.now(),
      action,
      costs,
      estimated_dollar_cost: this.calculateDollarCost(costs),
    };

    this.costs.push(entry);
    return entry;
  }

  /**
   * Calculate estimated dollar cost
   */
  private calculateDollarCost(costs: CostEntry["costs"]): number {
    let total = 0;

    if (costs.tokens) {
      total += (costs.tokens / 1000) * this.pricing.token_cost_per_1k;
    }

    if (costs.api_calls) {
      total += costs.api_calls * this.pricing.api_call_cost;
    }

    if (costs.compute_units) {
      total += costs.compute_units * this.pricing.compute_unit_cost;
    }

    return total;
  }

  /**
   * Get total costs
   */
  getTotalCosts(): {
    total_time_ms: number;
    total_tokens: number;
    total_api_calls: number;
    total_dollar_cost: number;
  } {
    let total_time_ms = 0;
    let total_tokens = 0;
    let total_api_calls = 0;
    let total_dollar_cost = 0;

    for (const entry of this.costs) {
      total_time_ms += entry.costs.time_ms;
      total_tokens += entry.costs.tokens || 0;
      total_api_calls += entry.costs.api_calls || 0;
      total_dollar_cost += entry.estimated_dollar_cost || 0;
    }

    return {
      total_time_ms,
      total_tokens,
      total_api_calls,
      total_dollar_cost,
    };
  }

  /**
   * Get costs by action
   */
  getCostsByAction(action: string): CostEntry[] {
    return this.costs.filter((c) => c.action === action);
  }

  /**
   * Get costs in time range
   */
  getCostsInTimeRange(start_ms: number, end_ms: number): CostEntry[] {
    return this.costs.filter(
      (c) => c.timestamp >= start_ms && c.timestamp <= end_ms,
    );
  }

  /**
   * Get most expensive actions
   */
  getMostExpensive(limit: number = 10): CostEntry[] {
    return [...this.costs]
      .sort(
        (a, b) =>
          (b.estimated_dollar_cost || 0) - (a.estimated_dollar_cost || 0),
      )
      .slice(0, limit);
  }

  /**
   * Update pricing
   */
  updatePricing(pricing: Partial<typeof this.pricing>): void {
    this.pricing = { ...this.pricing, ...pricing };
  }

  /**
   * Get average cost per action type
   */
  getAverageCostByAction(): Record<string, number> {
    const actionCosts: Record<string, number[]> = {};

    for (const entry of this.costs) {
      if (!actionCosts[entry.action]) {
        actionCosts[entry.action] = [];
      }
      actionCosts[entry.action].push(entry.estimated_dollar_cost || 0);
    }

    const averages: Record<string, number> = {};
    for (const [action, costs] of Object.entries(actionCosts)) {
      averages[action] = costs.reduce((sum, c) => sum + c, 0) / costs.length;
    }

    return averages;
  }

  /**
   * Clear all cost data
   */
  clear(): void {
    this.costs = [];
  }
}

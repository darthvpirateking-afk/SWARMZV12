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
export declare class CostTracker {
    private costs;
    private pricing;
    /**
     * Track cost for an action
     */
    track(action: string, costs: CostEntry['costs']): CostEntry;
    /**
     * Calculate estimated dollar cost
     */
    private calculateDollarCost;
    /**
     * Get total costs
     */
    getTotalCosts(): {
        total_time_ms: number;
        total_tokens: number;
        total_api_calls: number;
        total_dollar_cost: number;
    };
    /**
     * Get costs by action
     */
    getCostsByAction(action: string): CostEntry[];
    /**
     * Get costs in time range
     */
    getCostsInTimeRange(start_ms: number, end_ms: number): CostEntry[];
    /**
     * Get most expensive actions
     */
    getMostExpensive(limit?: number): CostEntry[];
    /**
     * Update pricing
     */
    updatePricing(pricing: Partial<typeof this.pricing>): void;
    /**
     * Get average cost per action type
     */
    getAverageCostByAction(): Record<string, number>;
    /**
     * Clear all cost data
     */
    clear(): void;
}
//# sourceMappingURL=cost_tracker.d.ts.map
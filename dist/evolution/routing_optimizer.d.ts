/**
 * Routing Optimizer - Optimizes task routing based on metrics
 * Part of Evolution Engine
 */
export interface RoutingRule {
    id: string;
    condition: string;
    worker_type: string;
    priority: number;
    success_rate: number;
    usage_count: number;
    created_at: number;
}
export declare class RoutingOptimizer {
    private rules;
    /**
     * Add a routing rule
     */
    addRule(condition: string, worker_type: string, priority?: number): RoutingRule;
    /**
     * Find best route for a task
     */
    findRoute(task_action: string, context: Record<string, any>): string | null;
    /**
     * Evaluate if condition matches
     */
    private evaluateCondition;
    /**
     * Update rule performance
     */
    updatePerformance(rule_id: string, success: boolean): void;
    /**
     * Get all rules
     */
    getRules(): RoutingRule[];
    /**
     * Remove poorly performing rules
     */
    pruneRules(min_success_rate?: number, min_usage?: number): number;
    /**
     * Get optimization suggestions
     */
    getSuggestions(): Array<{
        type: string;
        rule_id: string;
        suggestion: string;
        reason: string;
    }>;
    /**
     * Clear all rules
     */
    clear(): void;
}
//# sourceMappingURL=routing_optimizer.d.ts.map
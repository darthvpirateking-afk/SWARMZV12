"use strict";
/**
 * Routing Optimizer - Optimizes task routing based on metrics
 * Part of Evolution Engine
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.RoutingOptimizer = void 0;
class RoutingOptimizer {
    constructor() {
        this.rules = new Map();
    }
    /**
     * Add a routing rule
     */
    addRule(condition, worker_type, priority = 1) {
        const rule = {
            id: `rule_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            condition,
            worker_type,
            priority,
            success_rate: 0.5,
            usage_count: 0,
            created_at: Date.now()
        };
        this.rules.set(rule.id, rule);
        return rule;
    }
    /**
     * Find best route for a task
     */
    findRoute(task_action, context) {
        const matchingRules = Array.from(this.rules.values())
            .filter(rule => this.evaluateCondition(rule.condition, task_action, context))
            .sort((a, b) => {
            // Sort by priority first, then success rate
            if (a.priority !== b.priority) {
                return b.priority - a.priority;
            }
            return b.success_rate - a.success_rate;
        });
        if (matchingRules.length > 0) {
            matchingRules[0].usage_count++;
            return matchingRules[0].worker_type;
        }
        return null;
    }
    /**
     * Evaluate if condition matches
     */
    evaluateCondition(condition, task_action, context) {
        // Simple pattern matching for now
        // Could be expanded to full expression evaluation
        if (condition.includes('*')) {
            const pattern = condition.replace(/\*/g, '.*');
            return new RegExp(pattern).test(task_action);
        }
        return condition === task_action;
    }
    /**
     * Update rule performance
     */
    updatePerformance(rule_id, success) {
        const rule = this.rules.get(rule_id);
        if (!rule)
            return;
        // Update success rate with exponential moving average
        const alpha = 0.1;
        const new_result = success ? 1.0 : 0.0;
        rule.success_rate = (1 - alpha) * rule.success_rate + alpha * new_result;
    }
    /**
     * Get all rules
     */
    getRules() {
        return Array.from(this.rules.values());
    }
    /**
     * Remove poorly performing rules
     */
    pruneRules(min_success_rate = 0.3, min_usage = 10) {
        let pruned = 0;
        for (const [id, rule] of this.rules) {
            if (rule.usage_count >= min_usage && rule.success_rate < min_success_rate) {
                this.rules.delete(id);
                pruned++;
            }
        }
        return pruned;
    }
    /**
     * Get optimization suggestions
     */
    getSuggestions() {
        const suggestions = [];
        for (const rule of this.rules.values()) {
            // Suggest removing low-performing rules
            if (rule.usage_count > 20 && rule.success_rate < 0.3) {
                suggestions.push({
                    type: 'remove',
                    rule_id: rule.id,
                    suggestion: `Remove rule for ${rule.condition}`,
                    reason: `Low success rate: ${(rule.success_rate * 100).toFixed(1)}%`
                });
            }
            // Suggest promoting high-performing rules
            if (rule.usage_count > 50 && rule.success_rate > 0.8 && rule.priority < 10) {
                suggestions.push({
                    type: 'promote',
                    rule_id: rule.id,
                    suggestion: `Increase priority for ${rule.condition}`,
                    reason: `High success rate: ${(rule.success_rate * 100).toFixed(1)}%`
                });
            }
        }
        return suggestions;
    }
    /**
     * Clear all rules
     */
    clear() {
        this.rules.clear();
    }
}
exports.RoutingOptimizer = RoutingOptimizer;
//# sourceMappingURL=routing_optimizer.js.map
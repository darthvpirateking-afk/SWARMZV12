"use strict";
/**
 * Decision Engine - Determines best course of action
 * Part of Cognition Core
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.DecisionEngine = void 0;
class DecisionEngine {
    /**
     * Make a decision about how to handle a task
     */
    decide(task, plan) {
        const confidence = this.assessConfidence(task, plan);
        const should_execute = this.shouldExecute(task, confidence);
        return {
            task_id: task.id,
            should_execute,
            execution_plan: should_execute ? plan : null,
            rationale: this.generateRationale(task, plan, should_execute),
            alternatives: this.findAlternatives(task),
            confidence
        };
    }
    assessConfidence(task, plan) {
        let confidence = 0.5;
        // Boost confidence for safe tasks
        if (task.safety_level === 'safe') {
            confidence += 0.3;
        }
        // Boost confidence for simple plans
        if (plan.steps.length <= 3) {
            confidence += 0.1;
        }
        // Boost confidence for tasks with high priority
        if (task.priority >= 8) {
            confidence += 0.1;
        }
        return Math.min(confidence, 1.0);
    }
    shouldExecute(task, confidence) {
        // Never execute blocked tasks
        if (task.safety_level === 'blocked') {
            return false;
        }
        // Execute high-confidence safe tasks
        if (task.safety_level === 'safe' && confidence >= 0.7) {
            return true;
        }
        // Tasks needing confirmation require explicit approval
        if (task.safety_level === 'needs_confirm') {
            return false; // Will be handled by commit controller
        }
        return confidence >= 0.8;
    }
    generateRationale(task, plan, should_execute) {
        if (!should_execute) {
            if (task.safety_level === 'blocked') {
                return 'Task blocked due to safety concerns';
            }
            if (task.safety_level === 'needs_confirm') {
                return 'Task requires explicit confirmation';
            }
            return 'Confidence level too low for automatic execution';
        }
        return `Executing task with ${plan.steps.length} steps, estimated time ${plan.estimated_time_ms}ms`;
    }
    findAlternatives(task) {
        const alternatives = [];
        if (task.action === 'execute') {
            alternatives.push('query for more information first');
            alternatives.push('break down into smaller steps');
        }
        if (task.action === 'query') {
            alternatives.push('check cached results');
            alternatives.push('narrow the scope');
        }
        return alternatives;
    }
    /**
     * Re-evaluate a decision based on new information
     */
    reevaluate(decision, new_info) {
        // Could adjust confidence based on new information
        return {
            ...decision,
            confidence: Math.min(decision.confidence + 0.1, 1.0)
        };
    }
}
exports.DecisionEngine = DecisionEngine;
//# sourceMappingURL=decision_engine.js.map
"use strict";
/**
 * Planner - Chooses best action for a task
 * Part of Cognition Core
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.Planner = void 0;
class Planner {
    /**
     * Create an execution plan for a task packet
     */
    plan(task) {
        const steps = this.determineSteps(task);
        return {
            task_id: task.id,
            steps,
            estimated_time_ms: this.estimateTime(steps),
            required_workers: this.identifyWorkers(steps),
            dependencies: this.extractDependencies(task)
        };
    }
    determineSteps(task) {
        const steps = [];
        // Always start with scout to gather information
        steps.push({
            order: 1,
            action: 'scout',
            worker_type: 'scout',
            parameters: {
                target: task.action,
                context: task.parameters
            },
            timeout_ms: 5000
        });
        // If it's an execution task, add builder
        if (task.action !== 'query' && task.action !== 'clarify') {
            steps.push({
                order: 2,
                action: 'build',
                worker_type: 'builder',
                parameters: task.parameters,
                timeout_ms: 30000
            });
            // Always verify execution results
            steps.push({
                order: 3,
                action: 'verify',
                worker_type: 'verify',
                parameters: {
                    expected: task.parameters
                },
                timeout_ms: 10000
            });
        }
        return steps;
    }
    estimateTime(steps) {
        return steps.reduce((total, step) => total + step.timeout_ms, 0);
    }
    identifyWorkers(steps) {
        return [...new Set(steps.map(step => step.worker_type))];
    }
    extractDependencies(task) {
        // Extract any dependencies from task parameters
        const deps = [];
        if (task.parameters.file) {
            deps.push(task.parameters.file);
        }
        return deps;
    }
    /**
     * Optimize plan based on constraints
     */
    optimize(plan, constraints) {
        if (constraints.max_time_ms && plan.estimated_time_ms > constraints.max_time_ms) {
            // Reduce timeouts proportionally
            const ratio = constraints.max_time_ms / plan.estimated_time_ms;
            plan.steps = plan.steps.map(step => ({
                ...step,
                timeout_ms: Math.floor(step.timeout_ms * ratio)
            }));
            plan.estimated_time_ms = constraints.max_time_ms;
        }
        return plan;
    }
}
exports.Planner = Planner;
//# sourceMappingURL=planner.js.map
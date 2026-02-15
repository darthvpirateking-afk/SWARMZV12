"use strict";
/**
 * Risk Gate - Determines if an action is safe
 * Part of Cognition Core
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.RiskGate = void 0;
class RiskGate {
    constructor() {
        this.riskyPatterns = [
            'delete',
            'remove',
            'destroy',
            'drop',
            'truncate',
            'format',
            'wipe'
        ];
    }
    /**
     * Assess risk for a task
     */
    assess(task) {
        const risk_level = this.calculateRiskLevel(task);
        const warnings = this.identifyWarnings(task);
        const can_proceed = this.canProceed(risk_level, task.safety_level);
        return {
            task_id: task.id,
            risk_level,
            can_proceed,
            warnings,
            required_approvals: this.getRequiredApprovals(risk_level),
            mitigation_steps: this.getMitigationSteps(risk_level, task)
        };
    }
    calculateRiskLevel(task) {
        const action = task.action.toLowerCase();
        // Critical risk
        if (this.riskyPatterns.some(pattern => action.includes(pattern))) {
            return 'critical';
        }
        // High risk - write operations
        if (action.includes('write') || action.includes('modify') || action.includes('update')) {
            return 'high';
        }
        // Medium risk - execution operations
        if (action.includes('execute') || action.includes('run')) {
            return 'medium';
        }
        // Low risk - read operations
        return 'low';
    }
    identifyWarnings(task) {
        const warnings = [];
        const action = task.action.toLowerCase();
        if (this.riskyPatterns.some(pattern => action.includes(pattern))) {
            warnings.push('This action is destructive and cannot be undone');
        }
        if (action.includes('write') || action.includes('modify')) {
            warnings.push('This action will modify existing data');
        }
        if (task.parameters.file) {
            warnings.push(`Will affect file: ${task.parameters.file}`);
        }
        return warnings;
    }
    canProceed(risk_level, safety_level) {
        if (safety_level === 'blocked') {
            return false;
        }
        if (risk_level === 'critical') {
            return false; // Always require manual approval
        }
        if (risk_level === 'high' && safety_level !== 'safe') {
            return false;
        }
        return true;
    }
    getRequiredApprovals(risk_level) {
        switch (risk_level) {
            case 'critical':
                return ['operator', 'system_admin'];
            case 'high':
                return ['operator'];
            case 'medium':
                return ['automatic_with_logging'];
            default:
                return [];
        }
    }
    getMitigationSteps(risk_level, task) {
        const steps = [];
        if (risk_level === 'high' || risk_level === 'critical') {
            steps.push('Create backup before execution');
            steps.push('Enable rollback capability');
            steps.push('Log all changes');
        }
        if (risk_level === 'medium') {
            steps.push('Log execution details');
            steps.push('Set execution timeout');
        }
        return steps;
    }
    /**
     * Override risk assessment (operator sovereignty)
     */
    override(assessment, operator_approval) {
        if (operator_approval) {
            return {
                ...assessment,
                can_proceed: true,
                required_approvals: []
            };
        }
        return assessment;
    }
}
exports.RiskGate = RiskGate;
//# sourceMappingURL=risk_gate.js.map
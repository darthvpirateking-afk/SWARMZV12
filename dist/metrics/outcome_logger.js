"use strict";
/**
 * Outcome Logger - Records every action
 * Part of Measurement Spine - intelligence source
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.OutcomeLogger = void 0;
class OutcomeLogger {
    constructor() {
        this.outcomes = [];
        this.maxRecords = 10000;
    }
    /**
     * Log an outcome
     */
    log(metric, result, details) {
        const record = {
            id: `outcome_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
            metric,
            result,
            details
        };
        this.outcomes.push(record);
        // Keep only recent records
        if (this.outcomes.length > this.maxRecords) {
            this.outcomes = this.outcomes.slice(-this.maxRecords);
        }
        return record;
    }
    /**
     * Get outcomes for a specific action
     */
    getByAction(action) {
        return this.outcomes.filter(o => o.metric.action === action);
    }
    /**
     * Get successful outcomes
     */
    getSuccessful(limit) {
        const successful = this.outcomes.filter(o => o.result === 'success');
        return limit ? successful.slice(-limit) : successful;
    }
    /**
     * Get failed outcomes
     */
    getFailed(limit) {
        const failed = this.outcomes.filter(o => o.result === 'failure');
        return limit ? failed.slice(-limit) : failed;
    }
    /**
     * Get outcomes in time range
     */
    getInTimeRange(start_ms, end_ms) {
        return this.outcomes.filter(o => o.metric.timestamp >= start_ms &&
            o.metric.timestamp <= end_ms);
    }
    /**
     * Get statistics
     */
    getStats() {
        const total = this.outcomes.length;
        const successful = this.outcomes.filter(o => o.result === 'success').length;
        const failed = this.outcomes.filter(o => o.result === 'failure').length;
        const partial = this.outcomes.filter(o => o.result === 'partial').length;
        const total_duration = this.outcomes.reduce((sum, o) => sum + o.metric.duration_ms, 0);
        return {
            total,
            successful,
            failed,
            partial,
            success_rate: total > 0 ? successful / total : 0,
            average_duration_ms: total > 0 ? total_duration / total : 0
        };
    }
    /**
     * Export outcomes to JSON
     */
    export() {
        return JSON.stringify(this.outcomes, null, 2);
    }
    /**
     * Clear all outcomes
     */
    clear() {
        this.outcomes = [];
    }
}
exports.OutcomeLogger = OutcomeLogger;
//# sourceMappingURL=outcome_logger.js.map
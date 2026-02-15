/**
 * Outcome Logger - Records every action
 * Part of Measurement Spine - intelligence source
 */
import { MetricEntry } from '../types';
export interface OutcomeRecord {
    id: string;
    metric: MetricEntry;
    result: 'success' | 'failure' | 'partial';
    details: any;
}
export declare class OutcomeLogger {
    private outcomes;
    private maxRecords;
    /**
     * Log an outcome
     */
    log(metric: MetricEntry, result: 'success' | 'failure' | 'partial', details: any): OutcomeRecord;
    /**
     * Get outcomes for a specific action
     */
    getByAction(action: string): OutcomeRecord[];
    /**
     * Get successful outcomes
     */
    getSuccessful(limit?: number): OutcomeRecord[];
    /**
     * Get failed outcomes
     */
    getFailed(limit?: number): OutcomeRecord[];
    /**
     * Get outcomes in time range
     */
    getInTimeRange(start_ms: number, end_ms: number): OutcomeRecord[];
    /**
     * Get statistics
     */
    getStats(): {
        total: number;
        successful: number;
        failed: number;
        partial: number;
        success_rate: number;
        average_duration_ms: number;
    };
    /**
     * Export outcomes to JSON
     */
    export(): string;
    /**
     * Clear all outcomes
     */
    clear(): void;
}
//# sourceMappingURL=outcome_logger.d.ts.map
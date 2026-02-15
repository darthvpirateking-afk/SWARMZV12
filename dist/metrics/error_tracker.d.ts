/**
 * Error Tracker - Tracks and categorizes errors
 * Part of Measurement Spine
 */
export interface ErrorEntry {
    id: string;
    timestamp: number;
    action: string;
    error_type: string;
    error_message: string;
    stack_trace?: string;
    context: Record<string, any>;
    severity: 'low' | 'medium' | 'high' | 'critical';
    resolved: boolean;
}
export declare class ErrorTracker {
    private errors;
    private maxErrors;
    /**
     * Track an error
     */
    track(action: string, error: Error, context: Record<string, any>, severity?: ErrorEntry['severity']): ErrorEntry;
    /**
     * Mark error as resolved
     */
    resolve(error_id: string): boolean;
    /**
     * Get unresolved errors
     */
    getUnresolved(): ErrorEntry[];
    /**
     * Get errors by severity
     */
    getBySeverity(severity: ErrorEntry['severity']): ErrorEntry[];
    /**
     * Get errors by action
     */
    getByAction(action: string): ErrorEntry[];
    /**
     * Get recent errors
     */
    getRecent(limit?: number): ErrorEntry[];
    /**
     * Get error patterns (most common errors)
     */
    getPatterns(): Array<{
        error_type: string;
        count: number;
        last_seen: number;
    }>;
    /**
     * Get error statistics
     */
    getStats(): {
        total: number;
        unresolved: number;
        by_severity: Record<string, number>;
        by_action: Record<string, number>;
        error_rate: number;
    };
    /**
     * Clear all errors
     */
    clear(): void;
}
//# sourceMappingURL=error_tracker.d.ts.map
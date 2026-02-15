/**
 * Performance Index - Tracks system performance
 * Part of Measurement Spine
 */
export interface PerformanceMetric {
    timestamp: number;
    metric_type: 'throughput' | 'latency' | 'success_rate' | 'efficiency';
    value: number;
    context: string;
}
export declare class PerformanceIndex {
    private metrics;
    private rollingWindow;
    /**
     * Record a performance metric
     */
    record(metric_type: PerformanceMetric['metric_type'], value: number, context: string): void;
    /**
     * Get current performance index (0-100)
     */
    getCurrentIndex(): number;
    /**
     * Get metrics by type
     */
    getByType(metric_type: PerformanceMetric['metric_type']): PerformanceMetric[];
    /**
     * Get average for metric type
     */
    getAverage(metric_type: PerformanceMetric['metric_type']): number;
    /**
     * Get trend (improving, declining, stable)
     */
    getTrend(metric_type: PerformanceMetric['metric_type']): 'improving' | 'declining' | 'stable';
    /**
     * Get performance summary
     */
    getSummary(): {
        current_index: number;
        throughput_avg: number;
        latency_avg: number;
        success_rate_avg: number;
        efficiency_avg: number;
        trends: Record<string, string>;
    };
    /**
     * Clear all metrics
     */
    clear(): void;
}
//# sourceMappingURL=performance_index.d.ts.map
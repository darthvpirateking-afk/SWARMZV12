/**
 * Performance Index - Tracks system performance
 * Part of Measurement Spine
 */

export interface PerformanceMetric {
  timestamp: number;
  metric_type: "throughput" | "latency" | "success_rate" | "efficiency";
  value: number;
  context: string;
}

export class PerformanceIndex {
  private metrics: PerformanceMetric[] = [];
  private rollingWindow = 1000; // Keep last 1000 metrics

  /**
   * Record a performance metric
   */
  record(
    metric_type: PerformanceMetric["metric_type"],
    value: number,
    context: string,
  ): void {
    this.metrics.push({
      timestamp: Date.now(),
      metric_type,
      value,
      context,
    });

    // Keep only rolling window
    if (this.metrics.length > this.rollingWindow) {
      this.metrics = this.metrics.slice(-this.rollingWindow);
    }
  }

  /**
   * Get current performance index (0-100)
   */
  getCurrentIndex(): number {
    if (this.metrics.length === 0) return 50; // Default baseline

    const recentMetrics = this.metrics.slice(-100);
    let score = 0;
    let count = 0;

    for (const metric of recentMetrics) {
      switch (metric.metric_type) {
        case "success_rate":
          score += metric.value * 100; // Already 0-1
          count++;
          break;
        case "efficiency":
          score += metric.value * 100; // Already 0-1
          count++;
          break;
        case "latency":
          // Lower is better, normalize to 0-100
          score += Math.max(0, 100 - metric.value / 100);
          count++;
          break;
        case "throughput":
          // Higher is better, cap at 100
          score += Math.min(100, metric.value);
          count++;
          break;
      }
    }

    return count > 0 ? score / count : 50;
  }

  /**
   * Get metrics by type
   */
  getByType(
    metric_type: PerformanceMetric["metric_type"],
  ): PerformanceMetric[] {
    return this.metrics.filter((m) => m.metric_type === metric_type);
  }

  /**
   * Get average for metric type
   */
  getAverage(metric_type: PerformanceMetric["metric_type"]): number {
    const metrics = this.getByType(metric_type);
    if (metrics.length === 0) return 0;

    const sum = metrics.reduce((total, m) => total + m.value, 0);
    return sum / metrics.length;
  }

  /**
   * Get trend (improving, declining, stable)
   */
  getTrend(
    metric_type: PerformanceMetric["metric_type"],
  ): "improving" | "declining" | "stable" {
    const metrics = this.getByType(metric_type);
    if (metrics.length < 10) return "stable";

    const recent = metrics.slice(-10);
    const older = metrics.slice(-20, -10);

    const recentAvg =
      recent.reduce((sum, m) => sum + m.value, 0) / recent.length;
    const olderAvg = older.reduce((sum, m) => sum + m.value, 0) / older.length;

    const threshold = 0.05; // 5% change threshold
    const change = (recentAvg - olderAvg) / olderAvg;

    if (change > threshold) return "improving";
    if (change < -threshold) return "declining";
    return "stable";
  }

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
  } {
    return {
      current_index: this.getCurrentIndex(),
      throughput_avg: this.getAverage("throughput"),
      latency_avg: this.getAverage("latency"),
      success_rate_avg: this.getAverage("success_rate"),
      efficiency_avg: this.getAverage("efficiency"),
      trends: {
        throughput: this.getTrend("throughput"),
        latency: this.getTrend("latency"),
        success_rate: this.getTrend("success_rate"),
        efficiency: this.getTrend("efficiency"),
      },
    };
  }

  /**
   * Clear all metrics
   */
  clear(): void {
    this.metrics = [];
  }
}

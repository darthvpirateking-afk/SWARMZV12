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
  severity: "low" | "medium" | "high" | "critical";
  resolved: boolean;
}

export class ErrorTracker {
  private errors: ErrorEntry[] = [];
  private maxErrors = 1000;

  /**
   * Track an error
   */
  track(
    action: string,
    error: Error,
    context: Record<string, any>,
    severity: ErrorEntry["severity"] = "medium",
  ): ErrorEntry {
    const entry: ErrorEntry = {
      id: `error_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      action,
      error_type: error.name,
      error_message: error.message,
      stack_trace: error.stack,
      context,
      severity,
      resolved: false,
    };

    this.errors.push(entry);

    // Keep only recent errors
    if (this.errors.length > this.maxErrors) {
      this.errors = this.errors.slice(-this.maxErrors);
    }

    return entry;
  }

  /**
   * Mark error as resolved
   */
  resolve(error_id: string): boolean {
    const error = this.errors.find((e) => e.id === error_id);
    if (error) {
      error.resolved = true;
      return true;
    }
    return false;
  }

  /**
   * Get unresolved errors
   */
  getUnresolved(): ErrorEntry[] {
    return this.errors.filter((e) => !e.resolved);
  }

  /**
   * Get errors by severity
   */
  getBySeverity(severity: ErrorEntry["severity"]): ErrorEntry[] {
    return this.errors.filter((e) => e.severity === severity);
  }

  /**
   * Get errors by action
   */
  getByAction(action: string): ErrorEntry[] {
    return this.errors.filter((e) => e.action === action);
  }

  /**
   * Get recent errors
   */
  getRecent(limit: number = 10): ErrorEntry[] {
    return this.errors.slice(-limit).reverse();
  }

  /**
   * Get error patterns (most common errors)
   */
  getPatterns(): Array<{
    error_type: string;
    count: number;
    last_seen: number;
  }> {
    const patterns = new Map<string, { count: number; last_seen: number }>();

    for (const error of this.errors) {
      const key = `${error.error_type}:${error.error_message}`;
      const existing = patterns.get(key);

      if (existing) {
        existing.count++;
        existing.last_seen = Math.max(existing.last_seen, error.timestamp);
      } else {
        patterns.set(key, { count: 1, last_seen: error.timestamp });
      }
    }

    return Array.from(patterns.entries())
      .map(([error_type, data]) => ({ error_type, ...data }))
      .sort((a, b) => b.count - a.count);
  }

  /**
   * Get error statistics
   */
  getStats(): {
    total: number;
    unresolved: number;
    by_severity: Record<string, number>;
    by_action: Record<string, number>;
    error_rate: number; // errors per hour
  } {
    const total = this.errors.length;
    const unresolved = this.getUnresolved().length;

    const by_severity: Record<string, number> = {
      low: 0,
      medium: 0,
      high: 0,
      critical: 0,
    };

    const by_action: Record<string, number> = {};

    for (const error of this.errors) {
      by_severity[error.severity]++;
      by_action[error.action] = (by_action[error.action] || 0) + 1;
    }

    // Calculate error rate (errors per hour)
    const hour_ms = 3600000;
    const now = Date.now();
    const recent_errors = this.errors.filter(
      (e) => now - e.timestamp < hour_ms,
    );
    const error_rate = recent_errors.length;

    return {
      total,
      unresolved,
      by_severity,
      by_action,
      error_rate,
    };
  }

  /**
   * Clear all errors
   */
  clear(): void {
    this.errors = [];
  }
}

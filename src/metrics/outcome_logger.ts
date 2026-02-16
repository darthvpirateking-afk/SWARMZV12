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

export class OutcomeLogger {
  private outcomes: OutcomeRecord[] = [];
  private maxRecords: number = 10000;

  /**
   * Log an outcome
   */
  log(metric: MetricEntry, result: 'success' | 'failure' | 'partial', details: any): OutcomeRecord {
    const record: OutcomeRecord = {
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
  getByAction(action: string): OutcomeRecord[] {
    return this.outcomes.filter(o => o.metric.action === action);
  }

  /**
   * Get successful outcomes
   */
  getSuccessful(limit?: number): OutcomeRecord[] {
    const successful = this.outcomes.filter(o => o.result === 'success');
    return limit ? successful.slice(-limit) : successful;
  }

  /**
   * Get failed outcomes
   */
  getFailed(limit?: number): OutcomeRecord[] {
    const failed = this.outcomes.filter(o => o.result === 'failure');
    return limit ? failed.slice(-limit) : failed;
  }

  /**
   * Get outcomes in time range
   */
  getInTimeRange(start_ms: number, end_ms: number): OutcomeRecord[] {
    return this.outcomes.filter(o => 
      o.metric.timestamp >= start_ms && 
      o.metric.timestamp <= end_ms
    );
  }

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
  } {
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
  export(): string {
    return JSON.stringify(this.outcomes, null, 2);
  }

  /**
   * Clear all outcomes
   */
  clear(): void {
    this.outcomes = [];
  }
}

/**
 * Result Merger - Combines worker results
 * Part of Swarm Orchestrator
 */

import { WorkerResult } from '../types';

export interface MergedResult {
  task_id: string;
  overall_status: 'success' | 'failure' | 'partial';
  combined_data: any;
  all_artifacts: string[];
  total_cost: {
    time_ms: number;
    tokens?: number;
    api_calls?: number;
  };
  worker_count: number;
  error_summary?: string[];
}

export class ResultMerger {
  /**
   * Merge multiple worker results into a single result
   */
  merge(results: WorkerResult[]): MergedResult {
    const task_id = results[0]?.task_id || 'unknown';
    const overall_status = this.determineOverallStatus(results);
    const combined_data = this.combineData(results);
    const all_artifacts = this.collectArtifacts(results);
    const total_cost = this.sumCosts(results);
    const error_summary = this.collectErrors(results);
    
    return {
      task_id,
      overall_status,
      combined_data,
      all_artifacts,
      total_cost,
      worker_count: results.length,
      error_summary: error_summary.length > 0 ? error_summary : undefined
    };
  }

  private determineOverallStatus(results: WorkerResult[]): 'success' | 'failure' | 'partial' {
    const successCount = results.filter(r => r.status === 'success').length;
    const failureCount = results.filter(r => r.status === 'failure').length;
    
    if (failureCount === 0) {
      return 'success';
    }
    
    if (successCount === 0) {
      return 'failure';
    }
    
    return 'partial';
  }

  private combineData(results: WorkerResult[]): any {
    const combined: any = {
      results: results.map(r => ({
        status: r.status,
        data: r.data
      }))
    };
    
    // Extract successful data
    const successfulData = results
      .filter(r => r.status === 'success')
      .map(r => r.data);
    
    if (successfulData.length > 0) {
      combined.successful_outputs = successfulData;
    }
    
    return combined;
  }

  private collectArtifacts(results: WorkerResult[]): string[] {
    const artifacts = new Set<string>();
    
    for (const result of results) {
      for (const artifact of result.artifacts) {
        artifacts.add(artifact);
      }
    }
    
    return Array.from(artifacts);
  }

  private sumCosts(results: WorkerResult[]): {
    time_ms: number;
    tokens?: number;
    api_calls?: number;
  } {
    const total_time = results.reduce((sum, r) => sum + r.cost.time_ms, 0);
    const total_tokens = results.reduce((sum, r) => sum + (r.cost.tokens || 0), 0);
    const total_api_calls = results.reduce((sum, r) => sum + (r.cost.api_calls || 0), 0);
    
    return {
      time_ms: total_time,
      tokens: total_tokens > 0 ? total_tokens : undefined,
      api_calls: total_api_calls > 0 ? total_api_calls : undefined
    };
  }

  private collectErrors(results: WorkerResult[]): string[] {
    const errors: string[] = [];
    
    for (const result of results) {
      if (result.errors) {
        errors.push(...result.errors);
      }
    }
    
    return errors;
  }

  /**
   * Merge results from multiple tasks
   */
  mergeTasks(taskResults: Map<string, WorkerResult[]>): Map<string, MergedResult> {
    const merged = new Map<string, MergedResult>();
    
    for (const [task_id, results] of taskResults) {
      merged.set(task_id, this.merge(results));
    }
    
    return merged;
  }
}

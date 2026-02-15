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
export declare class ResultMerger {
    /**
     * Merge multiple worker results into a single result
     */
    merge(results: WorkerResult[]): MergedResult;
    private determineOverallStatus;
    private combineData;
    private collectArtifacts;
    private sumCosts;
    private collectErrors;
    /**
     * Merge results from multiple tasks
     */
    mergeTasks(taskResults: Map<string, WorkerResult[]>): Map<string, MergedResult>;
}
//# sourceMappingURL=result_merger.d.ts.map
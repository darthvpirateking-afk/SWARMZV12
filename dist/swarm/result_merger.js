"use strict";
/**
 * Result Merger - Combines worker results
 * Part of Swarm Orchestrator
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ResultMerger = void 0;
class ResultMerger {
    /**
     * Merge multiple worker results into a single result
     */
    merge(results) {
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
    determineOverallStatus(results) {
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
    combineData(results) {
        const combined = {
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
    collectArtifacts(results) {
        const artifacts = new Set();
        for (const result of results) {
            for (const artifact of result.artifacts) {
                artifacts.add(artifact);
            }
        }
        return Array.from(artifacts);
    }
    sumCosts(results) {
        const total_time = results.reduce((sum, r) => sum + r.cost.time_ms, 0);
        const total_tokens = results.reduce((sum, r) => sum + (r.cost.tokens || 0), 0);
        const total_api_calls = results.reduce((sum, r) => sum + (r.cost.api_calls || 0), 0);
        return {
            time_ms: total_time,
            tokens: total_tokens > 0 ? total_tokens : undefined,
            api_calls: total_api_calls > 0 ? total_api_calls : undefined
        };
    }
    collectErrors(results) {
        const errors = [];
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
    mergeTasks(taskResults) {
        const merged = new Map();
        for (const [task_id, results] of taskResults) {
            merged.set(task_id, this.merge(results));
        }
        return merged;
    }
}
exports.ResultMerger = ResultMerger;
//# sourceMappingURL=result_merger.js.map
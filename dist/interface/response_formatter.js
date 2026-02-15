"use strict";
/**
 * Response Formatter - Formats output for the user
 * Part of Interface Layer
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ResponseFormatter = void 0;
class ResponseFormatter {
    /**
     * Format a successful result
     */
    formatSuccess(result) {
        return {
            type: 'success',
            message: `Task ${result.task_id} completed successfully`,
            data: result.data,
            metadata: {
                status: result.status,
                duration: `${result.cost.time_ms}ms`,
                artifacts: result.artifacts
            }
        };
    }
    /**
     * Format an error
     */
    formatError(error, context) {
        const errorMessage = error instanceof Error ? error.message : error;
        return {
            type: 'error',
            message: errorMessage,
            metadata: context
        };
    }
    /**
     * Format an info message
     */
    formatInfo(message, data) {
        return {
            type: 'info',
            message,
            data
        };
    }
    /**
     * Format a confirmation request
     */
    formatConfirmation(action, details) {
        return {
            type: 'confirmation',
            message: `Confirm action: ${action}`,
            data: details,
            metadata: {
                requires_user_input: true
            }
        };
    }
    /**
     * Format multiple results as a summary
     */
    formatSummary(results) {
        const successful = results.filter(r => r.status === 'success').length;
        const failed = results.filter(r => r.status === 'failure').length;
        const total_time = results.reduce((sum, r) => sum + r.cost.time_ms, 0);
        return {
            type: successful === results.length ? 'success' : 'info',
            message: `Completed ${results.length} tasks: ${successful} successful, ${failed} failed`,
            data: results.map(r => ({
                task_id: r.task_id,
                status: r.status
            })),
            metadata: {
                total_time_ms: total_time,
                success_rate: (successful / results.length * 100).toFixed(1) + '%'
            }
        };
    }
    /**
     * Convert formatted response to string for display
     */
    toString(response) {
        let output = `[${response.type.toUpperCase()}] ${response.message}`;
        if (response.data) {
            output += `\nData: ${JSON.stringify(response.data, null, 2)}`;
        }
        if (response.metadata) {
            output += `\nMetadata: ${JSON.stringify(response.metadata, null, 2)}`;
        }
        return output;
    }
}
exports.ResponseFormatter = ResponseFormatter;
//# sourceMappingURL=response_formatter.js.map
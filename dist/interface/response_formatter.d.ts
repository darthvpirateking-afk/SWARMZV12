/**
 * Response Formatter - Formats output for the user
 * Part of Interface Layer
 */
import { WorkerResult } from '../types';
export interface FormattedResponse {
    type: 'success' | 'error' | 'info' | 'confirmation';
    message: string;
    data?: any;
    metadata?: Record<string, any>;
}
export declare class ResponseFormatter {
    /**
     * Format a successful result
     */
    formatSuccess(result: WorkerResult): FormattedResponse;
    /**
     * Format an error
     */
    formatError(error: Error | string, context?: Record<string, any>): FormattedResponse;
    /**
     * Format an info message
     */
    formatInfo(message: string, data?: any): FormattedResponse;
    /**
     * Format a confirmation request
     */
    formatConfirmation(action: string, details: Record<string, any>): FormattedResponse;
    /**
     * Format multiple results as a summary
     */
    formatSummary(results: WorkerResult[]): FormattedResponse;
    /**
     * Convert formatted response to string for display
     */
    toString(response: FormattedResponse): string;
}
//# sourceMappingURL=response_formatter.d.ts.map
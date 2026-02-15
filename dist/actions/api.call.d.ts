/**
 * API Call Action - Makes external API calls
 * Part of Action Layer
 */
import { Action } from '../types';
export interface ApiCallParams {
    url: string;
    method: 'GET' | 'POST' | 'PUT' | 'DELETE' | 'PATCH';
    headers?: Record<string, string>;
    body?: any;
    timeout_ms?: number;
}
export declare class ApiCallAction implements Action {
    private params;
    private response?;
    constructor(params: ApiCallParams);
    /**
     * Preview the API call
     */
    preview(): Promise<string>;
    /**
     * Execute the API call
     */
    execute(): Promise<any>;
    /**
     * Rollback the API call (if possible)
     */
    rollback(): Promise<void>;
}
//# sourceMappingURL=api.call.d.ts.map
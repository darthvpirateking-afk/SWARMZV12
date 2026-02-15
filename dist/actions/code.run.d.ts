/**
 * Code Run Action - Executes code
 * Part of Action Layer
 */
import { Action } from '../types';
export interface CodeRunParams {
    code: string;
    language: 'typescript' | 'javascript' | 'python' | 'bash';
    timeout_ms?: number;
    environment?: Record<string, string>;
    working_directory?: string;
}
export declare class CodeRunAction implements Action {
    private params;
    private processId?;
    constructor(params: CodeRunParams);
    /**
     * Preview the code execution
     */
    preview(): Promise<string>;
    /**
     * Execute the code
     */
    execute(): Promise<any>;
    /**
     * Rollback the code execution
     */
    rollback(): Promise<void>;
}
//# sourceMappingURL=code.run.d.ts.map
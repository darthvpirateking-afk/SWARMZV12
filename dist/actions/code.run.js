"use strict";
/**
 * Code Run Action - Executes code
 * Part of Action Layer
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.CodeRunAction = void 0;
class CodeRunAction {
    constructor(params) {
        this.params = params;
    }
    /**
     * Preview the code execution
     */
    async preview() {
        return `Will execute ${this.params.language} code:\n` +
            `Working Directory: ${this.params.working_directory || 'current'}\n` +
            `Timeout: ${this.params.timeout_ms || 30000}ms\n` +
            `Environment variables: ${Object.keys(this.params.environment || {}).length}\n` +
            `Code:\n${this.params.code.substring(0, 300)}${this.params.code.length > 300 ? '...' : ''}`;
    }
    /**
     * Execute the code
     */
    async execute() {
        // In real implementation, this would:
        // 1. Create isolated execution environment
        // 2. Set up timeout
        // 3. Run the code
        // 4. Capture stdout/stderr
        // 5. Get exit code
        // 6. Clean up
        const startTime = Date.now();
        this.processId = Math.floor(Math.random() * 100000);
        // Simulate code execution
        const result = {
            action: 'code_run',
            language: this.params.language,
            exit_code: 0,
            stdout: 'Code executed successfully',
            stderr: '',
            duration_ms: Date.now() - startTime,
            process_id: this.processId
        };
        return result;
    }
    /**
     * Rollback the code execution
     */
    async rollback() {
        // Code execution rollback is complex:
        // 1. Kill process if still running
        // 2. Undo any file changes (if tracked)
        // 3. Restore any modified state
        if (this.processId) {
            console.log(`Terminating process ${this.processId} if still running`);
            // In real implementation: kill process
        }
        console.log('Warning: Code execution side effects may not be fully reversible');
    }
}
exports.CodeRunAction = CodeRunAction;
//# sourceMappingURL=code.run.js.map
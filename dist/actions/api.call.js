"use strict";
/**
 * API Call Action - Makes external API calls
 * Part of Action Layer
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.ApiCallAction = void 0;
class ApiCallAction {
    constructor(params) {
        this.params = params;
    }
    /**
     * Preview the API call
     */
    async preview() {
        return `Will make ${this.params.method} request to: ${this.params.url}\n` +
            `Headers: ${JSON.stringify(this.params.headers || {}, null, 2)}\n` +
            `Body: ${this.params.body ? JSON.stringify(this.params.body, null, 2) : 'none'}\n` +
            `Timeout: ${this.params.timeout_ms || 30000}ms`;
    }
    /**
     * Execute the API call
     */
    async execute() {
        // In real implementation, this would:
        // 1. Make the HTTP request
        // 2. Handle response
        // 3. Parse JSON if applicable
        // 4. Handle errors
        const startTime = Date.now();
        // Simulate API call
        this.response = {
            status: 200,
            data: { success: true },
            headers: {}
        };
        return {
            action: 'api_call',
            url: this.params.url,
            method: this.params.method,
            status: this.response.status,
            response: this.response.data,
            duration_ms: Date.now() - startTime
        };
    }
    /**
     * Rollback the API call (if possible)
     */
    async rollback() {
        // API calls often can't be rolled back
        // This would need to make compensating API calls if supported
        console.log('Warning: API calls may not be fully reversible');
        // Could make DELETE call if this was a POST/PUT
        // Could make PUT call to restore if this was a DELETE
    }
}
exports.ApiCallAction = ApiCallAction;
//# sourceMappingURL=api.call.js.map
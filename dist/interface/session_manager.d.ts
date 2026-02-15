/**
 * Session Manager - Maintains conversation continuity
 * Part of Interface Layer - the only thing the human talks to
 */
export interface Session {
    id: string;
    user_id: string;
    created_at: number;
    last_active: number;
    context: Map<string, any>;
}
export declare class SessionManager {
    private sessions;
    /**
     * Create a new session
     */
    createSession(user_id: string): Session;
    /**
     * Get existing session
     */
    getSession(session_id: string): Session | undefined;
    /**
     * Update session context
     */
    updateContext(session_id: string, key: string, value: any): void;
    /**
     * Clean up old sessions
     */
    cleanupSessions(max_age_ms: number): void;
    private generateSessionId;
}
//# sourceMappingURL=session_manager.d.ts.map
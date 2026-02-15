"use strict";
/**
 * Session Manager - Maintains conversation continuity
 * Part of Interface Layer - the only thing the human talks to
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.SessionManager = void 0;
class SessionManager {
    constructor() {
        this.sessions = new Map();
    }
    /**
     * Create a new session
     */
    createSession(user_id) {
        const session = {
            id: this.generateSessionId(),
            user_id,
            created_at: Date.now(),
            last_active: Date.now(),
            context: new Map()
        };
        this.sessions.set(session.id, session);
        return session;
    }
    /**
     * Get existing session
     */
    getSession(session_id) {
        const session = this.sessions.get(session_id);
        if (session) {
            session.last_active = Date.now();
        }
        return session;
    }
    /**
     * Update session context
     */
    updateContext(session_id, key, value) {
        const session = this.sessions.get(session_id);
        if (session) {
            session.context.set(key, value);
            session.last_active = Date.now();
        }
    }
    /**
     * Clean up old sessions
     */
    cleanupSessions(max_age_ms) {
        const now = Date.now();
        for (const [id, session] of this.sessions) {
            if (now - session.last_active > max_age_ms) {
                this.sessions.delete(id);
            }
        }
    }
    generateSessionId() {
        return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}
exports.SessionManager = SessionManager;
//# sourceMappingURL=session_manager.js.map
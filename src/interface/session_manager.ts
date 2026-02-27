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

export class SessionManager {
  private sessions: Map<string, Session> = new Map();

  /**
   * Create a new session
   */
  createSession(user_id: string): Session {
    const session: Session = {
      id: this.generateSessionId(),
      user_id,
      created_at: Date.now(),
      last_active: Date.now(),
      context: new Map(),
    };

    this.sessions.set(session.id, session);
    return session;
  }

  /**
   * Get existing session
   */
  getSession(session_id: string): Session | undefined {
    const session = this.sessions.get(session_id);
    if (session) {
      session.last_active = Date.now();
    }
    return session;
  }

  /**
   * Update session context
   */
  updateContext(session_id: string, key: string, value: any): void {
    const session = this.sessions.get(session_id);
    if (session) {
      session.context.set(key, value);
      session.last_active = Date.now();
    }
  }

  /**
   * Clean up old sessions
   */
  cleanupSessions(max_age_ms: number): void {
    const now = Date.now();
    for (const [id, session] of this.sessions) {
      if (now - session.last_active > max_age_ms) {
        this.sessions.delete(id);
      }
    }
  }

  private generateSessionId(): string {
    return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

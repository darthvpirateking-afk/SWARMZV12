"use strict";
/**
 * Task Structurer - Converts language to structured task
 * Part of Cognition Core - decides what should happen but never performs actions
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.TaskStructurer = void 0;
class TaskStructurer {
    /**
     * Convert parsed intent into a structured task packet
     */
    structure(intent, session_id) {
        const task_id = this.generateTaskId();
        return {
            id: task_id,
            intent: intent.raw_input,
            action: intent.extracted_action || this.inferAction(intent),
            parameters: this.buildParameters(intent),
            context: {
                session_id,
                timestamp: Date.now()
            },
            safety_level: this.assessSafetyLevel(intent),
            priority: this.calculatePriority(intent)
        };
    }
    inferAction(intent) {
        if (intent.type === 'question') {
            return 'query';
        }
        else if (intent.type === 'command') {
            return 'execute';
        }
        return 'clarify';
    }
    buildParameters(intent) {
        return {
            ...intent.entities,
            intent_type: intent.type,
            confidence: intent.confidence
        };
    }
    assessSafetyLevel(intent) {
        // Questions are safe
        if (intent.type === 'question') {
            return 'safe';
        }
        // Commands need confirmation by default
        if (intent.type === 'command') {
            const action = intent.extracted_action?.toLowerCase();
            // Dangerous actions are blocked
            if (action && ['delete', 'remove', 'destroy'].includes(action)) {
                return 'needs_confirm';
            }
            return 'needs_confirm';
        }
        return 'safe';
    }
    calculatePriority(intent) {
        // Higher confidence = higher priority
        return Math.floor(intent.confidence * 10);
    }
    generateTaskId() {
        return `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
}
exports.TaskStructurer = TaskStructurer;
//# sourceMappingURL=task_structurer.js.map
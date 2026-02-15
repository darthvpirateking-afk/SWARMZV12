/**
 * Task Structurer - Converts language to structured task
 * Part of Cognition Core - decides what should happen but never performs actions
 */
import { TaskPacket } from '../types';
import { ParsedIntent } from '../interface/intent_parser';
export declare class TaskStructurer {
    /**
     * Convert parsed intent into a structured task packet
     */
    structure(intent: ParsedIntent, session_id: string): TaskPacket;
    private inferAction;
    private buildParameters;
    private assessSafetyLevel;
    private calculatePriority;
    private generateTaskId;
}
//# sourceMappingURL=task_structurer.d.ts.map
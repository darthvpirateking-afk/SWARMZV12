/**
 * Task Structurer - Converts language to structured task
 * Part of Cognition Core - decides what should happen but never performs actions
 */

import { TaskPacket } from '../types';
import { ParsedIntent } from '../interface/intent_parser';

export class TaskStructurer {
  /**
   * Convert parsed intent into a structured task packet
   */
  structure(intent: ParsedIntent, session_id: string): TaskPacket {
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

  private inferAction(intent: ParsedIntent): string {
    if (intent.type === 'question') {
      return 'query';
    } else if (intent.type === 'command') {
      return 'execute';
    }
    return 'clarify';
  }

  private buildParameters(intent: ParsedIntent): Record<string, any> {
    return {
      ...intent.entities,
      intent_type: intent.type,
      confidence: intent.confidence
    };
  }

  private assessSafetyLevel(intent: ParsedIntent): 'safe' | 'needs_confirm' | 'blocked' {
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

  private calculatePriority(intent: ParsedIntent): number {
    // Higher confidence = higher priority
    return Math.floor(intent.confidence * 10);
  }

  private generateTaskId(): string {
    return `task_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
}

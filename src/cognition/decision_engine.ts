/**
 * Decision Engine - Determines best course of action
 * Part of Cognition Core
 */

import { TaskPacket } from '../types';
import { ExecutionPlan } from './planner';

export interface Decision {
  task_id: string;
  should_execute: boolean;
  execution_plan: ExecutionPlan | null;
  rationale: string;
  alternatives: string[];
  confidence: number;
}

export class DecisionEngine {
  /**
   * Make a decision about how to handle a task
   */
  decide(task: TaskPacket, plan: ExecutionPlan): Decision {
    const confidence = this.assessConfidence(task, plan);
    const should_execute = this.shouldExecute(task, confidence);
    
    return {
      task_id: task.id,
      should_execute,
      execution_plan: should_execute ? plan : null,
      rationale: this.generateRationale(task, plan, should_execute),
      alternatives: this.findAlternatives(task),
      confidence
    };
  }

  private assessConfidence(task: TaskPacket, plan: ExecutionPlan): number {
    let confidence = 0.5;
    
    // Boost confidence for safe tasks
    if (task.safety_level === 'safe') {
      confidence += 0.3;
    }
    
    // Boost confidence for simple plans
    if (plan.steps.length <= 3) {
      confidence += 0.1;
    }
    
    // Boost confidence for tasks with high priority
    if (task.priority >= 8) {
      confidence += 0.1;
    }
    
    return Math.min(confidence, 1.0);
  }

  private shouldExecute(task: TaskPacket, confidence: number): boolean {
    // Never execute blocked tasks
    if (task.safety_level === 'blocked') {
      return false;
    }
    
    // Execute high-confidence safe tasks
    if (task.safety_level === 'safe' && confidence >= 0.7) {
      return true;
    }
    
    // Tasks needing confirmation require explicit approval
    if (task.safety_level === 'needs_confirm') {
      return false; // Will be handled by commit controller
    }
    
    return confidence >= 0.8;
  }

  private generateRationale(task: TaskPacket, plan: ExecutionPlan, should_execute: boolean): string {
    if (!should_execute) {
      if (task.safety_level === 'blocked') {
        return 'Task blocked due to safety concerns';
      }
      if (task.safety_level === 'needs_confirm') {
        return 'Task requires explicit confirmation';
      }
      return 'Confidence level too low for automatic execution';
    }
    
    return `Executing task with ${plan.steps.length} steps, estimated time ${plan.estimated_time_ms}ms`;
  }

  private findAlternatives(task: TaskPacket): string[] {
    const alternatives: string[] = [];
    
    if (task.action === 'execute') {
      alternatives.push('query for more information first');
      alternatives.push('break down into smaller steps');
    }
    
    if (task.action === 'query') {
      alternatives.push('check cached results');
      alternatives.push('narrow the scope');
    }
    
    return alternatives;
  }

  /**
   * Re-evaluate a decision based on new information
   */
  reevaluate(decision: Decision, new_info: Record<string, any>): Decision {
    // Could adjust confidence based on new information
    return {
      ...decision,
      confidence: Math.min(decision.confidence + 0.1, 1.0)
    };
  }
}

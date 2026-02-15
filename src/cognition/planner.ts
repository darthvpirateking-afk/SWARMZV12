/**
 * Planner - Chooses best action for a task
 * Part of Cognition Core
 */

import { TaskPacket } from '../types';

export interface ExecutionPlan {
  task_id: string;
  steps: ExecutionStep[];
  estimated_time_ms: number;
  required_workers: string[];
  dependencies: string[];
}

export interface ExecutionStep {
  order: number;
  action: string;
  worker_type: 'scout' | 'builder' | 'verify';
  parameters: Record<string, any>;
  timeout_ms: number;
}

export class Planner {
  /**
   * Create an execution plan for a task packet
   */
  plan(task: TaskPacket): ExecutionPlan {
    const steps = this.determineSteps(task);
    
    return {
      task_id: task.id,
      steps,
      estimated_time_ms: this.estimateTime(steps),
      required_workers: this.identifyWorkers(steps),
      dependencies: this.extractDependencies(task)
    };
  }

  private determineSteps(task: TaskPacket): ExecutionStep[] {
    const steps: ExecutionStep[] = [];
    
    // Always start with scout to gather information
    steps.push({
      order: 1,
      action: 'scout',
      worker_type: 'scout',
      parameters: {
        target: task.action,
        context: task.parameters
      },
      timeout_ms: 5000
    });
    
    // If it's an execution task, add builder
    if (task.action !== 'query' && task.action !== 'clarify') {
      steps.push({
        order: 2,
        action: 'build',
        worker_type: 'builder',
        parameters: task.parameters,
        timeout_ms: 30000
      });
      
      // Always verify execution results
      steps.push({
        order: 3,
        action: 'verify',
        worker_type: 'verify',
        parameters: {
          expected: task.parameters
        },
        timeout_ms: 10000
      });
    }
    
    return steps;
  }

  private estimateTime(steps: ExecutionStep[]): number {
    return steps.reduce((total, step) => total + step.timeout_ms, 0);
  }

  private identifyWorkers(steps: ExecutionStep[]): string[] {
    return [...new Set(steps.map(step => step.worker_type))];
  }

  private extractDependencies(task: TaskPacket): string[] {
    // Extract any dependencies from task parameters
    const deps: string[] = [];
    
    if (task.parameters.file) {
      deps.push(task.parameters.file);
    }
    
    return deps;
  }

  /**
   * Optimize plan based on constraints
   */
  optimize(plan: ExecutionPlan, constraints: { max_time_ms?: number }): ExecutionPlan {
    if (constraints.max_time_ms && plan.estimated_time_ms > constraints.max_time_ms) {
      // Reduce timeouts proportionally
      const ratio = constraints.max_time_ms / plan.estimated_time_ms;
      plan.steps = plan.steps.map(step => ({
        ...step,
        timeout_ms: Math.floor(step.timeout_ms * ratio)
      }));
      plan.estimated_time_ms = constraints.max_time_ms;
    }
    
    return plan;
  }
}

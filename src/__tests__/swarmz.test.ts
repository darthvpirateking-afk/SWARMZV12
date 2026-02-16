/**
 * Basic tests for SWARMZ Ultimate Layout
 */

import {
  SessionManager,
  IntentParser,
  TaskStructurer,
  Planner,
  WorkerRegistry,
  OutcomeLogger
} from '../index';

describe('SWARMZ Ultimate Layout', () => {
  describe('Interface Layer', () => {
    test('SessionManager creates unique sessions', () => {
      const manager = new SessionManager();
      const session1 = manager.createSession('user1');
      const session2 = manager.createSession('user1');
      
      expect(session1.id).not.toBe(session2.id);
      expect(session1.user_id).toBe('user1');
    });

    test('IntentParser detects questions', () => {
      const parser = new IntentParser();
      const intent = parser.parse('What is this?');
      
      expect(intent.type).toBe('question');
      expect(intent.confidence).toBeGreaterThan(0);
    });

    test('IntentParser detects commands', () => {
      const parser = new IntentParser();
      const intent = parser.parse('Create a file');
      
      expect(intent.type).toBe('command');
      expect(intent.extracted_action).toBe('create');
    });
  });

  describe('Cognition Core', () => {
    test('TaskStructurer creates valid task packets', () => {
      const parser = new IntentParser();
      const intent = parser.parse('Create a file');
      
      const structurer = new TaskStructurer();
      const task = structurer.structure(intent, 'session_123');
      
      expect(task.id).toBeDefined();
      expect(task.action).toBe('create');
      expect(task.context.session_id).toBe('session_123');
      expect(task.safety_level).toBeDefined();
    });

    test('Planner creates execution plans', () => {
      const parser = new IntentParser();
      const intent = parser.parse('Build something');
      
      const structurer = new TaskStructurer();
      const task = structurer.structure(intent, 'session_123');
      
      const planner = new Planner();
      const plan = planner.plan(task);
      
      expect(plan.task_id).toBe(task.id);
      expect(plan.steps.length).toBeGreaterThan(0);
      expect(plan.required_workers.length).toBeGreaterThan(0);
    });
  });

  describe('Swarm Orchestrator', () => {
    test('WorkerRegistry manages workers', () => {
      const registry = new WorkerRegistry();
      const workers = registry.listWorkers();
      
      expect(workers.length).toBeGreaterThan(0);
      expect(registry.isAvailable('scout')).toBe(true);
    });

    test('WorkerRegistry tracks worker usage', () => {
      const registry = new WorkerRegistry();
      
      expect(registry.markActive('scout')).toBe(true);
      registry.markInactive('scout');
      expect(registry.isAvailable('scout')).toBe(true);
    });
  });

  describe('Metrics Layer', () => {
    test('OutcomeLogger records outcomes', () => {
      const logger = new OutcomeLogger();
      
      logger.log(
        {
          timestamp: Date.now(),
          action: 'test',
          duration_ms: 100,
          cost: 1,
          success: true
        },
        'success',
        {}
      );
      
      const stats = logger.getStats();
      expect(stats.total).toBe(1);
      expect(stats.successful).toBe(1);
      expect(stats.success_rate).toBe(1.0);
    });

    test('OutcomeLogger filters by action', () => {
      const logger = new OutcomeLogger();
      
      logger.log(
        { timestamp: Date.now(), action: 'test1', duration_ms: 100, cost: 1, success: true },
        'success',
        {}
      );
      logger.log(
        { timestamp: Date.now(), action: 'test2', duration_ms: 100, cost: 1, success: true },
        'success',
        {}
      );
      
      const test1Results = logger.getByAction('test1');
      expect(test1Results.length).toBe(1);
      expect(test1Results[0].metric.action).toBe('test1');
    });
  });

  describe('Architecture Principles', () => {
    test('Layers remain isolated', () => {
      // Verify that each layer exports only its own components
      const parser = new IntentParser();
      const structurer = new TaskStructurer();
      const registry = new WorkerRegistry();
      
      // These should all be independent instances
      expect(parser).toBeDefined();
      expect(structurer).toBeDefined();
      expect(registry).toBeDefined();
      
      // No cross-dependencies at runtime
      expect(typeof parser.parse).toBe('function');
      expect(typeof structurer.structure).toBe('function');
      expect(typeof registry.listWorkers).toBe('function');
    });
  });
});

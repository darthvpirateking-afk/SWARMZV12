/**
 * SWARMZ Ultimate Layout - Main Entry Point
 * 
 * This is the minimal structure that avoids loops, agent chaos, and rewrite spirals.
 * 
 * Runtime Flow:
 * User speaks → Interface detects intent → Cognition creates TASK_PACKET
 * → Swarm spawns workers → Workers produce artifacts → Commit engine decides
 * → Actions execute → Metrics record → Evolution proposes improvements
 */

// Types
export * from './types';

// Interface Layer - Only thing the human talks to
export { SessionManager } from './interface/session_manager';
export { IntentParser } from './interface/intent_parser';
export { ModeSwitch } from './interface/mode_switch';
export { ResponseFormatter } from './interface/response_formatter';

// Cognition Core - Brain (decides, never performs actions)
export { TaskStructurer } from './cognition/task_structurer';
export { Planner } from './cognition/planner';
export { DecisionEngine } from './cognition/decision_engine';
export { RiskGate } from './cognition/risk_gate';
export { CommitController } from './cognition/commit_controller';

// Swarm Orchestrator - Delegation Layer (routes work, never thinks)
export { SwarmController } from './swarm/swarm_controller';
export { WorkerRegistry } from './swarm/worker_registry';
export { WorkerLimitsEnforcer } from './swarm/worker_limits';
export { ResultMerger } from './swarm/result_merger';

// Workers - Execution Units (stateless and replaceable)
export { ScoutWorker } from './workers/scout.worker';
export { BuilderWorker } from './workers/builder.worker';
export { VerifyWorker } from './workers/verify.worker';

// Action Layer - Real World Effects (only place allowed to touch reality)
export { FileWriteAction } from './actions/file.write';
export { ApiCallAction } from './actions/api.call';
export { MessageSendAction } from './actions/message.send';
export { CodeRunAction } from './actions/code.run';

// Commit Engine - Momentum System (prevents thinking forever)
export { PendingQueue } from './commit/pending_queue';
export { Countdown } from './commit/countdown';
export { ExecutionGuard } from './commit/execution_guard';

// Metrics - Measurement Spine (intelligence source)
export { OutcomeLogger } from './metrics/outcome_logger';
export { CostTracker } from './metrics/cost_tracker';
export { PerformanceIndex } from './metrics/performance_index';
export { ErrorTracker } from './metrics/error_tracker';

// Evolution - Safe Adaptation (improves without rewriting code)
export { WeightAdjuster } from './evolution/weight_adjuster';
export { RoutingOptimizer } from './evolution/routing_optimizer';
export { TemplateMutator } from './evolution/template_mutator';
export { PatchpackGenerator } from './evolution/patchpack_generator';

// Archive - Persists artifact packs to ./packs/
export { Archiver } from './archive/archiver';

// Factory - Autonomous artifact production loop
export { ArtifactFactory } from './factory/artifact_factory';

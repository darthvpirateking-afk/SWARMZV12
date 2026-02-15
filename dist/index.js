"use strict";
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
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __exportStar = (this && this.__exportStar) || function(m, exports) {
    for (var p in m) if (p !== "default" && !Object.prototype.hasOwnProperty.call(exports, p)) __createBinding(exports, m, p);
};
Object.defineProperty(exports, "__esModule", { value: true });
exports.PatchpackGenerator = exports.TemplateMutator = exports.RoutingOptimizer = exports.WeightAdjuster = exports.ErrorTracker = exports.PerformanceIndex = exports.CostTracker = exports.OutcomeLogger = exports.ExecutionGuard = exports.Countdown = exports.PendingQueue = exports.CodeRunAction = exports.MessageSendAction = exports.ApiCallAction = exports.FileWriteAction = exports.VerifyWorker = exports.BuilderWorker = exports.ScoutWorker = exports.ResultMerger = exports.WorkerLimitsEnforcer = exports.WorkerRegistry = exports.SwarmController = exports.CommitController = exports.RiskGate = exports.DecisionEngine = exports.Planner = exports.TaskStructurer = exports.ResponseFormatter = exports.ModeSwitch = exports.IntentParser = exports.SessionManager = void 0;
// Types
__exportStar(require("./types"), exports);
// Interface Layer - Only thing the human talks to
var session_manager_1 = require("./interface/session_manager");
Object.defineProperty(exports, "SessionManager", { enumerable: true, get: function () { return session_manager_1.SessionManager; } });
var intent_parser_1 = require("./interface/intent_parser");
Object.defineProperty(exports, "IntentParser", { enumerable: true, get: function () { return intent_parser_1.IntentParser; } });
var mode_switch_1 = require("./interface/mode_switch");
Object.defineProperty(exports, "ModeSwitch", { enumerable: true, get: function () { return mode_switch_1.ModeSwitch; } });
var response_formatter_1 = require("./interface/response_formatter");
Object.defineProperty(exports, "ResponseFormatter", { enumerable: true, get: function () { return response_formatter_1.ResponseFormatter; } });
// Cognition Core - Brain (decides, never performs actions)
var task_structurer_1 = require("./cognition/task_structurer");
Object.defineProperty(exports, "TaskStructurer", { enumerable: true, get: function () { return task_structurer_1.TaskStructurer; } });
var planner_1 = require("./cognition/planner");
Object.defineProperty(exports, "Planner", { enumerable: true, get: function () { return planner_1.Planner; } });
var decision_engine_1 = require("./cognition/decision_engine");
Object.defineProperty(exports, "DecisionEngine", { enumerable: true, get: function () { return decision_engine_1.DecisionEngine; } });
var risk_gate_1 = require("./cognition/risk_gate");
Object.defineProperty(exports, "RiskGate", { enumerable: true, get: function () { return risk_gate_1.RiskGate; } });
var commit_controller_1 = require("./cognition/commit_controller");
Object.defineProperty(exports, "CommitController", { enumerable: true, get: function () { return commit_controller_1.CommitController; } });
// Swarm Orchestrator - Delegation Layer (routes work, never thinks)
var swarm_controller_1 = require("./swarm/swarm_controller");
Object.defineProperty(exports, "SwarmController", { enumerable: true, get: function () { return swarm_controller_1.SwarmController; } });
var worker_registry_1 = require("./swarm/worker_registry");
Object.defineProperty(exports, "WorkerRegistry", { enumerable: true, get: function () { return worker_registry_1.WorkerRegistry; } });
var worker_limits_1 = require("./swarm/worker_limits");
Object.defineProperty(exports, "WorkerLimitsEnforcer", { enumerable: true, get: function () { return worker_limits_1.WorkerLimitsEnforcer; } });
var result_merger_1 = require("./swarm/result_merger");
Object.defineProperty(exports, "ResultMerger", { enumerable: true, get: function () { return result_merger_1.ResultMerger; } });
// Workers - Execution Units (stateless and replaceable)
var scout_worker_1 = require("./workers/scout.worker");
Object.defineProperty(exports, "ScoutWorker", { enumerable: true, get: function () { return scout_worker_1.ScoutWorker; } });
var builder_worker_1 = require("./workers/builder.worker");
Object.defineProperty(exports, "BuilderWorker", { enumerable: true, get: function () { return builder_worker_1.BuilderWorker; } });
var verify_worker_1 = require("./workers/verify.worker");
Object.defineProperty(exports, "VerifyWorker", { enumerable: true, get: function () { return verify_worker_1.VerifyWorker; } });
// Action Layer - Real World Effects (only place allowed to touch reality)
var file_write_1 = require("./actions/file.write");
Object.defineProperty(exports, "FileWriteAction", { enumerable: true, get: function () { return file_write_1.FileWriteAction; } });
var api_call_1 = require("./actions/api.call");
Object.defineProperty(exports, "ApiCallAction", { enumerable: true, get: function () { return api_call_1.ApiCallAction; } });
var message_send_1 = require("./actions/message.send");
Object.defineProperty(exports, "MessageSendAction", { enumerable: true, get: function () { return message_send_1.MessageSendAction; } });
var code_run_1 = require("./actions/code.run");
Object.defineProperty(exports, "CodeRunAction", { enumerable: true, get: function () { return code_run_1.CodeRunAction; } });
// Commit Engine - Momentum System (prevents thinking forever)
var pending_queue_1 = require("./commit/pending_queue");
Object.defineProperty(exports, "PendingQueue", { enumerable: true, get: function () { return pending_queue_1.PendingQueue; } });
var countdown_1 = require("./commit/countdown");
Object.defineProperty(exports, "Countdown", { enumerable: true, get: function () { return countdown_1.Countdown; } });
var execution_guard_1 = require("./commit/execution_guard");
Object.defineProperty(exports, "ExecutionGuard", { enumerable: true, get: function () { return execution_guard_1.ExecutionGuard; } });
// Metrics - Measurement Spine (intelligence source)
var outcome_logger_1 = require("./metrics/outcome_logger");
Object.defineProperty(exports, "OutcomeLogger", { enumerable: true, get: function () { return outcome_logger_1.OutcomeLogger; } });
var cost_tracker_1 = require("./metrics/cost_tracker");
Object.defineProperty(exports, "CostTracker", { enumerable: true, get: function () { return cost_tracker_1.CostTracker; } });
var performance_index_1 = require("./metrics/performance_index");
Object.defineProperty(exports, "PerformanceIndex", { enumerable: true, get: function () { return performance_index_1.PerformanceIndex; } });
var error_tracker_1 = require("./metrics/error_tracker");
Object.defineProperty(exports, "ErrorTracker", { enumerable: true, get: function () { return error_tracker_1.ErrorTracker; } });
// Evolution - Safe Adaptation (improves without rewriting code)
var weight_adjuster_1 = require("./evolution/weight_adjuster");
Object.defineProperty(exports, "WeightAdjuster", { enumerable: true, get: function () { return weight_adjuster_1.WeightAdjuster; } });
var routing_optimizer_1 = require("./evolution/routing_optimizer");
Object.defineProperty(exports, "RoutingOptimizer", { enumerable: true, get: function () { return routing_optimizer_1.RoutingOptimizer; } });
var template_mutator_1 = require("./evolution/template_mutator");
Object.defineProperty(exports, "TemplateMutator", { enumerable: true, get: function () { return template_mutator_1.TemplateMutator; } });
var patchpack_generator_1 = require("./evolution/patchpack_generator");
Object.defineProperty(exports, "PatchpackGenerator", { enumerable: true, get: function () { return patchpack_generator_1.PatchpackGenerator; } });
//# sourceMappingURL=index.js.map
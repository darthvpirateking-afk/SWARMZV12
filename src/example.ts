/**
 * Example: Using SWARMZ Ultimate Layout
 *
 * This demonstrates the runtime flow through all layers
 */

import {
  // Interface Layer
  SessionManager,
  IntentParser,
  ModeSwitch,
  ResponseFormatter,

  // Cognition Core
  TaskStructurer,
  Planner,
  DecisionEngine,
  RiskGate,
  CommitController,

  // Swarm Orchestrator
  SwarmController,
  WorkerRegistry,

  // Metrics
  OutcomeLogger,
  CostTracker,
  PerformanceIndex,
  ErrorTracker,

  // Types
  TaskPacket,
} from "./index";

async function demonstrateSwarmz() {
  console.log("=".repeat(60));
  console.log("SWARMZ Ultimate Layout - Runtime Flow Demonstration");
  console.log("=".repeat(60));
  console.log();

  // 1. INTERFACE LAYER - User speaks
  console.log("1. Interface Layer: User Input");
  console.log("-".repeat(60));

  const sessionMgr = new SessionManager();
  const session = sessionMgr.createSession("user_001");
  console.log(`   Created session: ${session.id}`);

  const parser = new IntentParser();
  const userInput = "Create a new configuration file";
  const intent = parser.parse(userInput);
  console.log(
    `   Parsed intent: ${intent.type} (confidence: ${intent.confidence})`,
  );

  const modeSwitch = new ModeSwitch("companion");
  console.log(`   Mode: ${modeSwitch.getCurrentMode()}`);
  console.log();

  // 2. COGNITION CORE - Brain decides
  console.log("2. Cognition Core: Decision Making");
  console.log("-".repeat(60));

  const structurer = new TaskStructurer();
  const task = structurer.structure(intent, session.id);
  console.log(`   Task ID: ${task.id}`);
  console.log(`   Action: ${task.action}`);
  console.log(`   Safety Level: ${task.safety_level}`);

  const planner = new Planner();
  const plan = planner.plan(task);
  console.log(`   Plan: ${plan.steps.length} steps`);
  console.log(`   Workers needed: ${plan.required_workers.join(", ")}`);

  const decisionEngine = new DecisionEngine();
  const decision = decisionEngine.decide(task, plan);
  console.log(`   Decision: ${decision.should_execute ? "EXECUTE" : "BLOCK"}`);
  console.log(`   Confidence: ${decision.confidence.toFixed(2)}`);

  const riskGate = new RiskGate();
  const risk = riskGate.assess(task);
  console.log(`   Risk Level: ${risk.risk_level}`);
  console.log(`   Can Proceed: ${risk.can_proceed}`);

  const commitCtrl = new CommitController();
  const commit = commitCtrl.determineCommit(task, risk, decision);
  console.log(`   Commit State: ${commit.state}`);
  console.log(`   Auto Execute: ${commit.auto_execute}`);
  console.log();

  // 3. SWARM ORCHESTRATOR - Delegation
  console.log("3. Swarm Orchestrator: Worker Dispatch");
  console.log("-".repeat(60));

  const registry = new WorkerRegistry();
  const workers = registry.listWorkers();
  console.log(`   Registered workers: ${workers.length}`);
  for (const worker of workers) {
    console.log(`   - ${worker.type}: ${worker.capabilities.join(", ")}`);
  }

  const swarm = new SwarmController();
  console.log(`   Dispatching ${plan.steps.length} worker tasks...`);
  const results = await swarm.dispatch(plan, task);
  console.log(`   Completed: ${results.length} results`);
  console.log();

  // 4. METRICS - Record everything
  console.log("4. Metrics Layer: Recording Outcomes");
  console.log("-".repeat(60));

  const outcomeLogger = new OutcomeLogger();
  const costTracker = new CostTracker();
  const perfIndex = new PerformanceIndex();
  const errorTracker = new ErrorTracker();

  for (const result of results) {
    // Log outcome
    outcomeLogger.log(
      {
        timestamp: Date.now(),
        action: task.action,
        duration_ms: result.cost.time_ms,
        cost: 0.01,
        success: result.status === "success",
      },
      result.status,
      result.data,
    );

    // Track cost
    costTracker.track(task.action, result.cost);

    // Record performance
    perfIndex.record(
      "success_rate",
      result.status === "success" ? 1.0 : 0.0,
      task.action,
    );
  }

  const stats = outcomeLogger.getStats();
  console.log(`   Total outcomes: ${stats.total}`);
  console.log(`   Success rate: ${(stats.success_rate * 100).toFixed(1)}%`);

  const costs = costTracker.getTotalCosts();
  console.log(`   Total time: ${costs.total_time_ms}ms`);
  console.log(`   Estimated cost: $${costs.total_dollar_cost.toFixed(4)}`);

  const perfSummary = perfIndex.getSummary();
  console.log(
    `   Performance index: ${perfSummary.current_index.toFixed(1)}/100`,
  );
  console.log();

  // 5. INTERFACE - Format response
  console.log("5. Interface Layer: Response Formatting");
  console.log("-".repeat(60));

  const formatter = new ResponseFormatter();
  const response = formatter.formatSuccess(results[0]);
  console.log(`   Type: ${response.type}`);
  console.log(`   Message: ${response.message}`);
  console.log();

  console.log("=".repeat(60));
  console.log("Runtime Flow Complete!");
  console.log("=".repeat(60));
  console.log();
  console.log("Key Principles Demonstrated:");
  console.log("✓ No shortcuts - every layer was used in order");
  console.log("✓ Brain decided - Cognition never executed");
  console.log("✓ Swarm worked - Orchestrator delegated tasks");
  console.log("✓ Metrics recorded - All outcomes tracked");
  console.log("✓ Separation maintained - Each layer stayed isolated");
}

// Run the demonstration
demonstrateSwarmz().catch(console.error);

/**
 * Artifact Factory - Autonomous artifact production loop
 *
 * Continuous cycle: DETECT -> DECIDE -> BUILD -> VERIFY -> ARCHIVE -> RANK -> REPEAT
 * Primary output: artifact packs saved under ./packs/
 */

import { TaskPacket, WorkerResult, ArtifactPack } from "../types";
import { IntentParser, ParsedIntent } from "../interface/intent_parser";
import { TaskStructurer } from "../cognition/task_structurer";
import { Planner } from "../cognition/planner";
import { DecisionEngine } from "../cognition/decision_engine";
import { RiskGate } from "../cognition/risk_gate";
import { BuilderWorker } from "../workers/builder.worker";
import { VerifyWorker } from "../workers/verify.worker";
import { PerformanceIndex } from "../metrics/performance_index";
import { OutcomeLogger } from "../metrics/outcome_logger";
import { Archiver } from "../archive/archiver";

export interface FactoryCycleResult {
  pack: ArtifactPack;
  skipped: boolean;
  reason?: string;
}

export class ArtifactFactory {
  private parser: IntentParser;
  private structurer: TaskStructurer;
  private planner: Planner;
  private decisionEngine: DecisionEngine;
  private riskGate: RiskGate;
  private builder: BuilderWorker;
  private verifier: VerifyWorker;
  private perfIndex: PerformanceIndex;
  private outcomeLogger: OutcomeLogger;
  private archiver: Archiver;
  private running = false;
  private cycleCount = 0;

  constructor(packsDir: string = "./packs") {
    this.parser = new IntentParser();
    this.structurer = new TaskStructurer();
    this.planner = new Planner();
    this.decisionEngine = new DecisionEngine();
    this.riskGate = new RiskGate();
    this.builder = new BuilderWorker();
    this.verifier = new VerifyWorker();
    this.perfIndex = new PerformanceIndex();
    this.outcomeLogger = new OutcomeLogger();
    this.archiver = new Archiver(packsDir);
  }

  /**
   * Run a single DETECT -> DECIDE -> BUILD -> VERIFY -> ARCHIVE -> RANK cycle
   */
  async runCycle(
    input: string,
    sessionId: string = "factory",
  ): Promise<FactoryCycleResult> {
    const cycleStart = Date.now();
    this.cycleCount++;

    // --- DETECT ---
    const intent: ParsedIntent = this.parser.parse(input);
    const task: TaskPacket = this.structurer.structure(intent, sessionId);

    // --- DECIDE ---
    const plan = this.planner.plan(task);
    const risk = this.riskGate.assess(task);
    const decision = this.decisionEngine.decide(task, plan);

    // The factory acts as autonomous operator: auto-approve tasks that
    // need confirmation but are not blocked by the risk gate.
    const canProceed =
      risk.can_proceed &&
      (decision.should_execute || task.safety_level === "needs_confirm");

    if (!canProceed) {
      const skippedPack = this.buildPack(task, [], false, [], 0, cycleStart);
      return {
        pack: skippedPack,
        skipped: true,
        reason: decision.rationale,
      };
    }

    // --- BUILD ---
    const buildResult: WorkerResult = await this.builder.execute(task);

    // --- VERIFY ---
    const verifyResult: WorkerResult = await this.verifier.execute(task);
    const passed = verifyResult.status === "success";
    const errors = verifyResult.errors ?? [];

    // --- ARCHIVE ---
    const artifacts = buildResult.artifacts;
    const rank = this.computeRank(buildResult, verifyResult);
    const pack = this.buildPack(
      task,
      artifacts,
      passed,
      errors,
      rank,
      cycleStart,
    );
    this.archiver.save(pack);

    // --- RANK ---
    this.perfIndex.record("success_rate", passed ? 1.0 : 0.0, task.action);
    this.perfIndex.record("latency", Date.now() - cycleStart, task.action);
    this.outcomeLogger.log(
      {
        timestamp: Date.now(),
        action: task.action,
        duration_ms: Date.now() - cycleStart,
        cost: 0,
        success: passed,
      },
      passed ? "success" : "failure",
      { pack_id: pack.id },
    );

    return { pack, skipped: false };
  }

  /**
   * Run the factory loop continuously over an array of intents.
   * Stops after processing all intents or when stop() is called.
   */
  async run(
    intents: string[],
    sessionId: string = "factory",
  ): Promise<ArtifactPack[]> {
    this.running = true;
    const packs: ArtifactPack[] = [];

    for (const intent of intents) {
      if (!this.running) break;
      const result = await this.runCycle(intent, sessionId);
      packs.push(result.pack);
    }

    this.running = false;
    return packs;
  }

  /**
   * Signal the factory to stop after the current cycle
   */
  stop(): void {
    this.running = false;
  }

  /**
   * Return true while the factory loop is active
   */
  isRunning(): boolean {
    return this.running;
  }

  /**
   * Get number of completed cycles
   */
  getCycleCount(): number {
    return this.cycleCount;
  }

  /**
   * Get performance summary from the ranking layer
   */
  getPerformanceSummary() {
    return this.perfIndex.getSummary();
  }

  /**
   * Get outcome statistics
   */
  getStats() {
    return this.outcomeLogger.getStats();
  }

  /**
   * List all archived pack IDs
   */
  listPacks(): string[] {
    return this.archiver.list();
  }

  // --- Private helpers ---

  private buildPack(
    task: TaskPacket,
    artifacts: string[],
    passed: boolean,
    errors: string[],
    rank: number,
    cycleStart: number,
  ): ArtifactPack {
    return {
      id: `pack_${Date.now()}_${Math.random().toString(36).substring(2, 11)}`,
      task_id: task.id,
      intent: task.intent,
      artifacts,
      verification: {
        passed,
        checks: passed ? 3 : 0,
        errors,
      },
      rank,
      created_at: Date.now(),
      cycle_ms: Date.now() - cycleStart,
    };
  }

  private computeRank(
    buildResult: WorkerResult,
    verifyResult: WorkerResult,
  ): number {
    let score = 50; // baseline

    if (buildResult.status === "success") score += 25;
    if (verifyResult.status === "success") score += 25;

    // Penalize slow builds
    if (buildResult.cost.time_ms > 5000) score -= 10;

    return Math.max(0, Math.min(100, score));
  }
}

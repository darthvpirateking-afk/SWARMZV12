/**
 * Commit Controller - Produces commit state
 * Part of Cognition Core
 */

import { CommitState, TaskPacket } from "../types";
import { RiskAssessment } from "./risk_gate";
import { Decision } from "./decision_engine";

export interface CommitDecision {
  task_id: string;
  state: CommitState;
  auto_execute: boolean;
  requires_confirmation: boolean;
  countdown_seconds?: number;
  justification: string;
}

export class CommitController {
  private default_countdown_seconds = 5;

  /**
   * Determine commit state for a task
   */
  determineCommit(
    task: TaskPacket,
    risk: RiskAssessment,
    decision: Decision,
  ): CommitDecision {
    const state = this.calculateState(task, risk, decision);
    const auto_execute = this.canAutoExecute(state, risk);
    const countdown = auto_execute ? this.default_countdown_seconds : undefined;

    return {
      task_id: task.id,
      state,
      auto_execute,
      requires_confirmation: state === "NEEDS_CONFIRM",
      countdown_seconds: countdown,
      justification: this.generateJustification(state, risk, decision),
    };
  }

  private calculateState(
    task: TaskPacket,
    risk: RiskAssessment,
    decision: Decision,
  ): CommitState {
    // Blocked if risk doesn't allow
    if (!risk.can_proceed) {
      return "BLOCKED";
    }

    // Blocked if decision says no
    if (!decision.should_execute) {
      return "BLOCKED";
    }

    // Needs confirm for high/critical risk
    if (risk.risk_level === "high" || risk.risk_level === "critical") {
      return "NEEDS_CONFIRM";
    }

    // Needs confirm if task safety level requires it
    if (task.safety_level === "needs_confirm") {
      return "NEEDS_CONFIRM";
    }

    // Action ready for safe, low-risk tasks
    return "ACTION_READY";
  }

  private canAutoExecute(state: CommitState, risk: RiskAssessment): boolean {
    return state === "ACTION_READY" && risk.risk_level === "low";
  }

  private generateJustification(
    state: CommitState,
    risk: RiskAssessment,
    decision: Decision,
  ): string {
    switch (state) {
      case "ACTION_READY":
        return `Safe to execute: ${risk.risk_level} risk, confidence ${decision.confidence.toFixed(2)}`;
      case "NEEDS_CONFIRM":
        return `Requires confirmation: ${risk.risk_level} risk level`;
      case "BLOCKED":
        if (!risk.can_proceed) {
          return `Blocked by risk assessment: ${risk.warnings.join(", ")}`;
        }
        return `Blocked by decision engine: ${decision.rationale}`;
      default:
        return "Unknown state";
    }
  }

  /**
   * Process user confirmation
   */
  processConfirmation(
    commit: CommitDecision,
    confirmed: boolean,
  ): CommitDecision {
    if (!confirmed) {
      return {
        ...commit,
        state: "BLOCKED",
        auto_execute: false,
        justification: "Blocked by user rejection",
      };
    }

    return {
      ...commit,
      state: "ACTION_READY",
      auto_execute: true,
      requires_confirmation: false,
      justification: "Approved by user confirmation",
    };
  }

  /**
   * Update countdown
   */
  updateCountdown(commit: CommitDecision, seconds: number): CommitDecision {
    return {
      ...commit,
      countdown_seconds: seconds,
    };
  }
}

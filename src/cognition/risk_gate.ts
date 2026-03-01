/**
 * Risk Gate - Determines if an action is safe
 * Part of Cognition Core
 */

import { TaskPacket } from "../types";

export interface RiskAssessment {
  task_id: string;
  risk_level: "low" | "medium" | "high" | "critical";
  can_proceed: boolean;
  warnings: string[];
  required_approvals: string[];
  mitigation_steps: string[];
}

export class RiskGate {
  private riskyPatterns: string[] = [
    "delete",
    "remove",
    "destroy",
    "drop",
    "truncate",
    "format",
    "wipe",
  ];

  /**
   * Assess risk for a task
   */
  assess(task: TaskPacket): RiskAssessment {
    const risk_level = this.calculateRiskLevel(task);
    const warnings = this.identifyWarnings(task);
    const can_proceed = this.canProceed(risk_level, task.safety_level);

    return {
      task_id: task.id,
      risk_level,
      can_proceed,
      warnings,
      required_approvals: this.getRequiredApprovals(risk_level),
      mitigation_steps: this.getMitigationSteps(risk_level, task),
    };
  }

  private calculateRiskLevel(
    task: TaskPacket,
  ): "low" | "medium" | "high" | "critical" {
    const action = task.action.toLowerCase();

    // Critical risk
    if (this.riskyPatterns.some((pattern) => action.includes(pattern))) {
      return "critical";
    }

    // High risk - write operations
    if (
      action.includes("write") ||
      action.includes("modify") ||
      action.includes("update")
    ) {
      return "high";
    }

    // Medium risk - execution operations
    if (action.includes("execute") || action.includes("run")) {
      return "medium";
    }

    // Low risk - read operations
    return "low";
  }

  private identifyWarnings(task: TaskPacket): string[] {
    const warnings: string[] = [];
    const action = task.action.toLowerCase();

    if (this.riskyPatterns.some((pattern) => action.includes(pattern))) {
      warnings.push("This action is destructive and cannot be undone");
    }

    if (action.includes("write") || action.includes("modify")) {
      warnings.push("This action will modify existing data");
    }

    if (task.parameters.file) {
      warnings.push(`Will affect file: ${task.parameters.file}`);
    }

    return warnings;
  }

  private canProceed(risk_level: string, safety_level: string): boolean {
    if (safety_level === "blocked") {
      return false;
    }

    if (risk_level === "critical") {
      return false; // Always require manual approval
    }

    if (risk_level === "high" && safety_level !== "safe") {
      return false;
    }

    return true;
  }

  private getRequiredApprovals(risk_level: string): string[] {
    switch (risk_level) {
      case "critical":
        return ["operator", "system_admin"];
      case "high":
        return ["operator"];
      case "medium":
        return ["automatic_with_logging"];
      default:
        return [];
    }
  }

  private getMitigationSteps(risk_level: string, task: TaskPacket): string[] {
    const steps: string[] = [];

    if (risk_level === "high" || risk_level === "critical") {
      steps.push("Create backup before execution");
      steps.push("Enable rollback capability");
      steps.push("Log all changes");
    }

    if (risk_level === "medium") {
      steps.push("Log execution details");
      steps.push("Set execution timeout");
    }

    return steps;
  }

  /**
   * Override risk assessment (operator sovereignty)
   */
  override(
    assessment: RiskAssessment,
    operator_approval: boolean,
  ): RiskAssessment {
    if (operator_approval) {
      return {
        ...assessment,
        can_proceed: true,
        required_approvals: [],
      };
    }
    return assessment;
  }
}

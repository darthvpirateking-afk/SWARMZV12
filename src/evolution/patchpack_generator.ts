/**
 * Patchpack Generator - Generates patch packs for improvements
 * Part of Evolution Engine - never auto-applies
 */

import { PatchPack } from "../types";

export interface PatchProposal {
  file: string;
  current_version: string;
  proposed_change: string;
  reason: string;
  impact: "low" | "medium" | "high";
  confidence: number;
}

export class PatchpackGenerator {
  private proposals: PatchProposal[] = [];

  /**
   * Generate a patch pack from proposals
   */
  generate(proposals: PatchProposal[]): PatchPack {
    const version = this.generateVersion();

    const changes = proposals.map((p) => ({
      file: p.file,
      diff: this.generateDiff(p.current_version, p.proposed_change),
    }));

    const rationale = this.generateRationale(proposals);
    const metrics_justification = this.generateMetricsJustification(proposals);

    return {
      version,
      changes,
      rationale,
      metrics_justification,
    };
  }

  /**
   * Add a patch proposal
   */
  propose(proposal: PatchProposal): void {
    this.proposals.push(proposal);
  }

  /**
   * Generate diff between versions
   */
  private generateDiff(current: string, proposed: string): string {
    // Simplified diff generation
    // In real implementation, would use proper diff algorithm
    return `--- a/file\n+++ b/file\n${this.simpleDiff(current, proposed)}`;
  }

  private simpleDiff(current: string, proposed: string): string {
    const currentLines = current.split("\n");
    const proposedLines = proposed.split("\n");

    let diff = "";
    const maxLines = Math.max(currentLines.length, proposedLines.length);

    for (let i = 0; i < maxLines; i++) {
      if (currentLines[i] !== proposedLines[i]) {
        if (currentLines[i]) {
          diff += `- ${currentLines[i]}\n`;
        }
        if (proposedLines[i]) {
          diff += `+ ${proposedLines[i]}\n`;
        }
      }
    }

    return diff;
  }

  /**
   * Generate rationale for patch pack
   */
  private generateRationale(proposals: PatchProposal[]): string {
    const reasons = proposals.map((p) => `${p.file}: ${p.reason}`);
    return `Proposed improvements based on system metrics:\n${reasons.join("\n")}`;
  }

  /**
   * Generate metrics justification
   */
  private generateMetricsJustification(proposals: PatchProposal[]): string {
    const highConfidence = proposals.filter((p) => p.confidence > 0.8).length;
    const mediumConfidence = proposals.filter(
      (p) => p.confidence > 0.5 && p.confidence <= 0.8,
    ).length;

    return (
      `Based on observed performance:\n` +
      `- ${highConfidence} high-confidence improvements\n` +
      `- ${mediumConfidence} medium-confidence improvements\n` +
      `Average confidence: ${this.calculateAverageConfidence(proposals).toFixed(2)}`
    );
  }

  private calculateAverageConfidence(proposals: PatchProposal[]): number {
    if (proposals.length === 0) return 0;
    const sum = proposals.reduce((total, p) => total + p.confidence, 0);
    return sum / proposals.length;
  }

  /**
   * Generate version string
   */
  private generateVersion(): string {
    const date = new Date();
    return `patch_${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, "0")}${String(date.getDate()).padStart(2, "0")}_${Date.now()}`;
  }

  /**
   * Get all proposals
   */
  getProposals(): PatchProposal[] {
    return [...this.proposals];
  }

  /**
   * Clear proposals
   */
  clearProposals(): void {
    this.proposals = [];
  }

  /**
   * Filter proposals by impact
   */
  filterByImpact(impact: PatchProposal["impact"]): PatchProposal[] {
    return this.proposals.filter((p) => p.impact === impact);
  }

  /**
   * Filter proposals by confidence
   */
  filterByConfidence(minConfidence: number): PatchProposal[] {
    return this.proposals.filter((p) => p.confidence >= minConfidence);
  }

  /**
   * Export patch pack to file format
   */
  exportPatchPack(patchPack: PatchPack): string {
    return JSON.stringify(patchPack, null, 2);
  }
}

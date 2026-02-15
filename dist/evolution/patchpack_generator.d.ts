/**
 * Patchpack Generator - Generates patch packs for improvements
 * Part of Evolution Engine - never auto-applies
 */
import { PatchPack } from '../types';
export interface PatchProposal {
    file: string;
    current_version: string;
    proposed_change: string;
    reason: string;
    impact: 'low' | 'medium' | 'high';
    confidence: number;
}
export declare class PatchpackGenerator {
    private proposals;
    /**
     * Generate a patch pack from proposals
     */
    generate(proposals: PatchProposal[]): PatchPack;
    /**
     * Add a patch proposal
     */
    propose(proposal: PatchProposal): void;
    /**
     * Generate diff between versions
     */
    private generateDiff;
    private simpleDiff;
    /**
     * Generate rationale for patch pack
     */
    private generateRationale;
    /**
     * Generate metrics justification
     */
    private generateMetricsJustification;
    private calculateAverageConfidence;
    /**
     * Generate version string
     */
    private generateVersion;
    /**
     * Get all proposals
     */
    getProposals(): PatchProposal[];
    /**
     * Clear proposals
     */
    clearProposals(): void;
    /**
     * Filter proposals by impact
     */
    filterByImpact(impact: PatchProposal['impact']): PatchProposal[];
    /**
     * Filter proposals by confidence
     */
    filterByConfidence(minConfidence: number): PatchProposal[];
    /**
     * Export patch pack to file format
     */
    exportPatchPack(patchPack: PatchPack): string;
}
//# sourceMappingURL=patchpack_generator.d.ts.map
"use strict";
/**
 * Patchpack Generator - Generates patch packs for improvements
 * Part of Evolution Engine - never auto-applies
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.PatchpackGenerator = void 0;
class PatchpackGenerator {
    constructor() {
        this.proposals = [];
    }
    /**
     * Generate a patch pack from proposals
     */
    generate(proposals) {
        const version = this.generateVersion();
        const changes = proposals.map(p => ({
            file: p.file,
            diff: this.generateDiff(p.current_version, p.proposed_change)
        }));
        const rationale = this.generateRationale(proposals);
        const metrics_justification = this.generateMetricsJustification(proposals);
        return {
            version,
            changes,
            rationale,
            metrics_justification
        };
    }
    /**
     * Add a patch proposal
     */
    propose(proposal) {
        this.proposals.push(proposal);
    }
    /**
     * Generate diff between versions
     */
    generateDiff(current, proposed) {
        // Simplified diff generation
        // In real implementation, would use proper diff algorithm
        return `--- a/file\n+++ b/file\n${this.simpleDiff(current, proposed)}`;
    }
    simpleDiff(current, proposed) {
        const currentLines = current.split('\n');
        const proposedLines = proposed.split('\n');
        let diff = '';
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
    generateRationale(proposals) {
        const reasons = proposals.map(p => `${p.file}: ${p.reason}`);
        return `Proposed improvements based on system metrics:\n${reasons.join('\n')}`;
    }
    /**
     * Generate metrics justification
     */
    generateMetricsJustification(proposals) {
        const highConfidence = proposals.filter(p => p.confidence > 0.8).length;
        const mediumConfidence = proposals.filter(p => p.confidence > 0.5 && p.confidence <= 0.8).length;
        return `Based on observed performance:\n` +
            `- ${highConfidence} high-confidence improvements\n` +
            `- ${mediumConfidence} medium-confidence improvements\n` +
            `Average confidence: ${this.calculateAverageConfidence(proposals).toFixed(2)}`;
    }
    calculateAverageConfidence(proposals) {
        if (proposals.length === 0)
            return 0;
        const sum = proposals.reduce((total, p) => total + p.confidence, 0);
        return sum / proposals.length;
    }
    /**
     * Generate version string
     */
    generateVersion() {
        const date = new Date();
        return `patch_${date.getFullYear()}${String(date.getMonth() + 1).padStart(2, '0')}${String(date.getDate()).padStart(2, '0')}_${Date.now()}`;
    }
    /**
     * Get all proposals
     */
    getProposals() {
        return [...this.proposals];
    }
    /**
     * Clear proposals
     */
    clearProposals() {
        this.proposals = [];
    }
    /**
     * Filter proposals by impact
     */
    filterByImpact(impact) {
        return this.proposals.filter(p => p.impact === impact);
    }
    /**
     * Filter proposals by confidence
     */
    filterByConfidence(minConfidence) {
        return this.proposals.filter(p => p.confidence >= minConfidence);
    }
    /**
     * Export patch pack to file format
     */
    exportPatchPack(patchPack) {
        return JSON.stringify(patchPack, null, 2);
    }
}
exports.PatchpackGenerator = PatchpackGenerator;
//# sourceMappingURL=patchpack_generator.js.map
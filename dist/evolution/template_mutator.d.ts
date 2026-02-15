/**
 * Template Mutator - Adapts templates based on usage
 * Part of Evolution Engine
 */
export interface Template {
    id: string;
    name: string;
    pattern: string;
    parameters: Record<string, any>;
    usage_count: number;
    success_rate: number;
    last_used: number;
    created_at: number;
}
export interface Mutation {
    template_id: string;
    mutation_type: 'parameter_adjust' | 'pattern_modify' | 'merge' | 'split';
    changes: Record<string, any>;
    rationale: string;
}
export declare class TemplateMutator {
    private templates;
    private mutations;
    /**
     * Register a template
     */
    register(name: string, pattern: string, parameters: Record<string, any>): Template;
    /**
     * Use a template
     */
    use(template_id: string, success: boolean): void;
    /**
     * Propose mutations for underperforming templates
     */
    proposeMutations(): Mutation[];
    /**
     * Apply a mutation
     */
    applyMutation(mutation: Mutation): Template | null;
    /**
     * Find similar templates
     */
    private findSimilarTemplates;
    /**
     * Calculate similarity between templates
     */
    private calculateSimilarity;
    /**
     * Get all templates
     */
    getTemplates(): Template[];
    /**
     * Get mutation history
     */
    getMutationHistory(): Mutation[];
    /**
     * Clear all templates
     */
    clear(): void;
}
//# sourceMappingURL=template_mutator.d.ts.map
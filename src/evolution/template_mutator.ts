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

export class TemplateMutator {
  private templates: Map<string, Template> = new Map();
  private mutations: Mutation[] = [];

  /**
   * Register a template
   */
  register(name: string, pattern: string, parameters: Record<string, any>): Template {
    const template: Template = {
      id: `template_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      name,
      pattern,
      parameters,
      usage_count: 0,
      success_rate: 0.5,
      last_used: Date.now(),
      created_at: Date.now()
    };
    
    this.templates.set(template.id, template);
    return template;
  }

  /**
   * Use a template
   */
  use(template_id: string, success: boolean): void {
    const template = this.templates.get(template_id);
    if (!template) return;
    
    template.usage_count++;
    template.last_used = Date.now();
    
    // Update success rate
    const alpha = 0.1;
    const new_result = success ? 1.0 : 0.0;
    template.success_rate = (1 - alpha) * template.success_rate + alpha * new_result;
  }

  /**
   * Propose mutations for underperforming templates
   */
  proposeMutations(): Mutation[] {
    const proposals: Mutation[] = [];
    
    for (const template of this.templates.values()) {
      // Only mutate templates that have been used enough
      if (template.usage_count < 10) continue;
      
      // Mutate low-performing templates
      if (template.success_rate < 0.5) {
        proposals.push({
          template_id: template.id,
          mutation_type: 'parameter_adjust',
          changes: {
            timeout_increase: 1.5,
            retry_enabled: true
          },
          rationale: `Low success rate: ${(template.success_rate * 100).toFixed(1)}%`
        });
      }
      
      // Suggest splitting complex templates
      if (template.pattern.split('{{').length > 5) {
        proposals.push({
          template_id: template.id,
          mutation_type: 'split',
          changes: {
            split_into: 2
          },
          rationale: 'Template too complex, consider splitting'
        });
      }
    }
    
    // Suggest merging similar templates
    const similarPairs = this.findSimilarTemplates();
    for (const [id1, id2] of similarPairs) {
      proposals.push({
        template_id: id1,
        mutation_type: 'merge',
        changes: {
          merge_with: id2
        },
        rationale: 'Templates are similar, consider merging'
      });
    }
    
    return proposals;
  }

  /**
   * Apply a mutation
   */
  applyMutation(mutation: Mutation): Template | null {
    const template = this.templates.get(mutation.template_id);
    if (!template) return null;
    
    switch (mutation.mutation_type) {
      case 'parameter_adjust':
        template.parameters = { ...template.parameters, ...mutation.changes };
        break;
      
      case 'pattern_modify':
        if (mutation.changes.new_pattern) {
          template.pattern = mutation.changes.new_pattern;
        }
        break;
      
      case 'merge':
      case 'split':
        // These would create new templates
        break;
    }
    
    this.mutations.push(mutation);
    return template;
  }

  /**
   * Find similar templates
   */
  private findSimilarTemplates(): Array<[string, string]> {
    const pairs: Array<[string, string]> = [];
    const templates = Array.from(this.templates.values());
    
    for (let i = 0; i < templates.length; i++) {
      for (let j = i + 1; j < templates.length; j++) {
        const similarity = this.calculateSimilarity(templates[i], templates[j]);
        if (similarity > 0.8) {
          pairs.push([templates[i].id, templates[j].id]);
        }
      }
    }
    
    return pairs;
  }

  /**
   * Calculate similarity between templates
   */
  private calculateSimilarity(t1: Template, t2: Template): number {
    // Simple similarity based on pattern matching
    const words1 = t1.pattern.split(/\s+/);
    const words2 = t2.pattern.split(/\s+/);
    
    const common = words1.filter(w => words2.includes(w)).length;
    const total = Math.max(words1.length, words2.length);
    
    return total > 0 ? common / total : 0;
  }

  /**
   * Get all templates
   */
  getTemplates(): Template[] {
    return Array.from(this.templates.values());
  }

  /**
   * Get mutation history
   */
  getMutationHistory(): Mutation[] {
    return [...this.mutations];
  }

  /**
   * Clear all templates
   */
  clear(): void {
    this.templates.clear();
    this.mutations = [];
  }
}

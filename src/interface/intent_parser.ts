/**
 * Intent Parser - Detects question vs command
 * Part of Interface Layer
 */

export type IntentType = "question" | "command" | "clarification";

export interface ParsedIntent {
  type: IntentType;
  raw_input: string;
  extracted_action?: string;
  entities: Record<string, any>;
  confidence: number;
}

export class IntentParser {
  /**
   * Parse user input to determine intent
   */
  parse(input: string): ParsedIntent {
    const trimmed = input.trim();

    // Question patterns
    if (this.isQuestion(trimmed)) {
      return {
        type: "question",
        raw_input: input,
        entities: this.extractEntities(trimmed),
        confidence: 0.9,
      };
    }

    // Command patterns
    if (this.isCommand(trimmed)) {
      return {
        type: "command",
        raw_input: input,
        extracted_action: this.extractAction(trimmed),
        entities: this.extractEntities(trimmed),
        confidence: 0.85,
      };
    }

    // Default to clarification needed
    return {
      type: "clarification",
      raw_input: input,
      entities: {},
      confidence: 0.5,
    };
  }

  private isQuestion(input: string): boolean {
    const questionWords = [
      "what",
      "when",
      "where",
      "who",
      "why",
      "how",
      "is",
      "are",
      "can",
      "could",
      "would",
      "should",
    ];
    const lowerInput = input.toLowerCase();

    return (
      input.endsWith("?") ||
      questionWords.some((word) => lowerInput.startsWith(word + " "))
    );
  }

  private isCommand(input: string): boolean {
    const commandVerbs = [
      "create",
      "delete",
      "update",
      "run",
      "execute",
      "build",
      "deploy",
      "start",
      "stop",
      "write",
      "read",
    ];
    const lowerInput = input.toLowerCase();

    return commandVerbs.some((verb) => lowerInput.startsWith(verb + " "));
  }

  private extractAction(input: string): string {
    const words = input.split(" ");
    return words[0].toLowerCase();
  }

  private extractEntities(input: string): Record<string, any> {
    // Basic entity extraction - could be expanded
    const entities: Record<string, any> = {};

    // Extract file paths
    const fileMatch = input.match(/([\/\w.-]+\.(ts|js|json|md|py))/);
    if (fileMatch) {
      entities.file = fileMatch[1];
    }

    return entities;
  }
}

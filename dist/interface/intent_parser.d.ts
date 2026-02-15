/**
 * Intent Parser - Detects question vs command
 * Part of Interface Layer
 */
export type IntentType = 'question' | 'command' | 'clarification';
export interface ParsedIntent {
    type: IntentType;
    raw_input: string;
    extracted_action?: string;
    entities: Record<string, any>;
    confidence: number;
}
export declare class IntentParser {
    /**
     * Parse user input to determine intent
     */
    parse(input: string): ParsedIntent;
    private isQuestion;
    private isCommand;
    private extractAction;
    private extractEntities;
}
//# sourceMappingURL=intent_parser.d.ts.map
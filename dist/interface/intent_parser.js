"use strict";
/**
 * Intent Parser - Detects question vs command
 * Part of Interface Layer
 */
Object.defineProperty(exports, "__esModule", { value: true });
exports.IntentParser = void 0;
class IntentParser {
    /**
     * Parse user input to determine intent
     */
    parse(input) {
        const trimmed = input.trim();
        // Question patterns
        if (this.isQuestion(trimmed)) {
            return {
                type: 'question',
                raw_input: input,
                entities: this.extractEntities(trimmed),
                confidence: 0.9
            };
        }
        // Command patterns
        if (this.isCommand(trimmed)) {
            return {
                type: 'command',
                raw_input: input,
                extracted_action: this.extractAction(trimmed),
                entities: this.extractEntities(trimmed),
                confidence: 0.85
            };
        }
        // Default to clarification needed
        return {
            type: 'clarification',
            raw_input: input,
            entities: {},
            confidence: 0.5
        };
    }
    isQuestion(input) {
        const questionWords = ['what', 'when', 'where', 'who', 'why', 'how', 'is', 'are', 'can', 'could', 'would', 'should'];
        const lowerInput = input.toLowerCase();
        return input.endsWith('?') ||
            questionWords.some(word => lowerInput.startsWith(word + ' '));
    }
    isCommand(input) {
        const commandVerbs = ['create', 'delete', 'update', 'run', 'execute', 'build', 'deploy', 'start', 'stop', 'write', 'read'];
        const lowerInput = input.toLowerCase();
        return commandVerbs.some(verb => lowerInput.startsWith(verb + ' '));
    }
    extractAction(input) {
        const words = input.split(' ');
        return words[0].toLowerCase();
    }
    extractEntities(input) {
        // Basic entity extraction - could be expanded
        const entities = {};
        // Extract file paths
        const fileMatch = input.match(/([\/\w.-]+\.(ts|js|json|md|py))/);
        if (fileMatch) {
            entities.file = fileMatch[1];
        }
        return entities;
    }
}
exports.IntentParser = IntentParser;
//# sourceMappingURL=intent_parser.js.map
/**
 * Message Send Action - Sends messages to external systems
 * Part of Action Layer
 */
import { Action } from '../types';
export interface MessageSendParams {
    destination: string;
    message: string;
    channel?: string;
    priority?: 'low' | 'normal' | 'high' | 'urgent';
    metadata?: Record<string, any>;
}
export declare class MessageSendAction implements Action {
    private params;
    private messageId?;
    constructor(params: MessageSendParams);
    /**
     * Preview the message send
     */
    preview(): Promise<string>;
    /**
     * Execute the message send
     */
    execute(): Promise<any>;
    /**
     * Rollback the message send
     */
    rollback(): Promise<void>;
}
//# sourceMappingURL=message.send.d.ts.map
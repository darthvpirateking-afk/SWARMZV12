/**
 * File Write Action - Writes to filesystem
 * Part of Action Layer - the only place allowed to touch reality
 */
import { Action } from '../types';
export interface FileWriteParams {
    path: string;
    content: string;
    mode?: 'create' | 'overwrite' | 'append';
}
export declare class FileWriteAction implements Action {
    private params;
    private backup?;
    constructor(params: FileWriteParams);
    /**
     * Preview the file write operation
     */
    preview(): Promise<string>;
    /**
     * Execute the file write
     */
    execute(): Promise<any>;
    /**
     * Rollback the file write
     */
    rollback(): Promise<void>;
}
//# sourceMappingURL=file.write.d.ts.map
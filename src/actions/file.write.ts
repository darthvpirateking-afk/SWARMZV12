/**
 * File Write Action - Writes to filesystem
 * Part of Action Layer - the only place allowed to touch reality
 */

import { Action } from "../types";

export interface FileWriteParams {
  path: string;
  content: string;
  mode?: "create" | "overwrite" | "append";
}

export class FileWriteAction implements Action {
  private params: FileWriteParams;
  private backup?: string;

  constructor(params: FileWriteParams) {
    this.params = params;
  }

  /**
   * Preview the file write operation
   */
  async preview(): Promise<string> {
    return (
      `Will write to file: ${this.params.path}\n` +
      `Mode: ${this.params.mode || "create"}\n` +
      `Content length: ${this.params.content.length} bytes\n` +
      `Preview:\n${this.params.content.substring(0, 200)}...`
    );
  }

  /**
   * Execute the file write
   */
  async execute(): Promise<any> {
    // In real implementation, this would:
    // 1. Check if file exists
    // 2. Create backup if overwriting
    // 3. Write the file
    // 4. Verify write succeeded

    this.backup = `backup_${this.params.path}_${Date.now()}`;

    return {
      action: "file_write",
      path: this.params.path,
      bytes_written: this.params.content.length,
      backup: this.backup,
      timestamp: Date.now(),
    };
  }

  /**
   * Rollback the file write
   */
  async rollback(): Promise<void> {
    // In real implementation, this would:
    // 1. Restore from backup if available
    // 2. Delete newly created file if was create mode
    // 3. Verify rollback succeeded

    if (this.backup) {
      console.log(`Rolling back: restoring from ${this.backup}`);
    }
  }
}

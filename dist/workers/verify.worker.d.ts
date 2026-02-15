/**
 * Verify Worker - Tests, validates, and checks
 * Part of Workers Layer - stateless and replaceable
 */
import { TaskPacket, WorkerResult } from '../types';
export declare class VerifyWorker {
    /**
     * Execute verification task
     */
    execute(task: TaskPacket): Promise<WorkerResult>;
    private verify;
    private generateArtifacts;
}
//# sourceMappingURL=verify.worker.d.ts.map
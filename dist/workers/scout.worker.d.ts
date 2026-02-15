/**
 * Scout Worker - Reads, searches, and analyzes
 * Part of Workers Layer - stateless and replaceable
 */
import { TaskPacket, WorkerResult } from '../types';
export declare class ScoutWorker {
    /**
     * Execute scout task
     */
    execute(task: TaskPacket): Promise<WorkerResult>;
    private scout;
    private generateArtifacts;
}
//# sourceMappingURL=scout.worker.d.ts.map
/**
 * Builder Worker - Creates, modifies, and builds
 * Part of Workers Layer - stateless and replaceable
 */
import { TaskPacket, WorkerResult } from '../types';
export declare class BuilderWorker {
    /**
     * Execute builder task
     */
    execute(task: TaskPacket): Promise<WorkerResult>;
    private build;
    private generateArtifacts;
}
//# sourceMappingURL=builder.worker.d.ts.map
import React from "react";

export type MissionTaskStatus = "queued" | "running" | "blocked" | "done" | "failed";

export interface MissionTask {
  id: string;
  title: string;
  status: MissionTaskStatus;
}

interface MissionKanbanProps {
  tasks: MissionTask[];
}

const COLUMNS: { key: MissionTaskStatus; label: string }[] = [
  { key: "queued", label: "Queued" },
  { key: "running", label: "Running" },
  { key: "blocked", label: "Blocked" },
  { key: "done", label: "Done" },
  { key: "failed", label: "Failed" },
];

export function MissionKanban({ tasks }: MissionKanbanProps) {
  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(5, minmax(0, 1fr))", gap: 8 }}>
      {COLUMNS.map((column) => {
        const bucket = tasks.filter((task) => task.status === column.key);
        return (
          <div
            key={column.key}
            style={{
              border: "1px solid rgba(0,170,255,0.2)",
              borderRadius: 8,
              padding: 8,
              minHeight: 120,
              background: "rgba(255,255,255,0.02)",
            }}
          >
            <div style={{ fontSize: 12, fontWeight: 700, marginBottom: 6 }}>{column.label}</div>
            <div style={{ display: "grid", gap: 6 }}>
              {bucket.map((task) => (
                <div
                  key={task.id}
                  style={{
                    fontSize: 11,
                    border: "1px solid rgba(0,170,255,0.15)",
                    borderRadius: 6,
                    padding: "5px 6px",
                  }}
                >
                  {task.title}
                </div>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

export default MissionKanban;

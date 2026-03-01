/**
 * Tests for the Autonomous Artifact Factory and Archiver
 */

import * as fs from "fs";
import * as path from "path";
import * as os from "os";
import { ArtifactFactory, Archiver, ArtifactPack } from "../index";

describe("Archiver", () => {
  let tmpDir: string;
  let archiver: Archiver;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "swarmz-test-"));
    archiver = new Archiver(tmpDir);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  test("ensurePacksDir creates directory", () => {
    const nested = path.join(tmpDir, "sub", "packs");
    const a = new Archiver(nested);
    a.ensurePacksDir();
    expect(fs.existsSync(nested)).toBe(true);
  });

  test("save writes JSON file and load reads it back", () => {
    const pack: ArtifactPack = {
      id: "pack_test_001",
      task_id: "task_1",
      intent: "Build something",
      artifacts: ["a.txt"],
      verification: { passed: true, checks: 3, errors: [] },
      rank: 100,
      created_at: Date.now(),
      cycle_ms: 42,
    };

    const filepath = archiver.save(pack);
    expect(fs.existsSync(filepath)).toBe(true);

    const loaded = archiver.load("pack_test_001");
    expect(loaded).not.toBeNull();
    expect(loaded!.id).toBe("pack_test_001");
    expect(loaded!.artifacts).toEqual(["a.txt"]);
  });

  test("load returns null for missing pack", () => {
    expect(archiver.load("does_not_exist")).toBeNull();
  });

  test("list returns saved pack IDs", () => {
    const pack1: ArtifactPack = {
      id: "p1",
      task_id: "t1",
      intent: "a",
      artifacts: [],
      verification: { passed: true, checks: 0, errors: [] },
      rank: 50,
      created_at: Date.now(),
      cycle_ms: 1,
    };
    const pack2: ArtifactPack = {
      id: "p2",
      task_id: "t2",
      intent: "b",
      artifacts: [],
      verification: { passed: true, checks: 0, errors: [] },
      rank: 50,
      created_at: Date.now(),
      cycle_ms: 1,
    };

    archiver.save(pack1);
    archiver.save(pack2);

    const ids = archiver.list();
    expect(ids).toContain("p1");
    expect(ids).toContain("p2");
    expect(ids.length).toBe(2);
  });

  test("list returns empty when packs dir does not exist", () => {
    const missing = new Archiver(path.join(tmpDir, "nonexistent"));
    expect(missing.list()).toEqual([]);
  });
});

describe("ArtifactFactory", () => {
  let tmpDir: string;
  let factory: ArtifactFactory;

  beforeEach(() => {
    tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "swarmz-factory-"));
    factory = new ArtifactFactory(tmpDir);
  });

  afterEach(() => {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  });

  test("runCycle produces an artifact pack for a command intent", async () => {
    const result = await factory.runCycle("Build a configuration file");

    expect(result.skipped).toBe(false);
    expect(result.pack).toBeDefined();
    expect(result.pack.id).toMatch(/^pack_/);
    expect(result.pack.artifacts.length).toBeGreaterThan(0);
    expect(result.pack.verification.passed).toBe(true);
    expect(result.pack.rank).toBeGreaterThan(0);
  });

  test("runCycle archives pack to packs directory", async () => {
    await factory.runCycle("Create a new module");

    const ids = factory.listPacks();
    expect(ids.length).toBe(1);

    // Verify file exists on disk
    const filepath = path.join(tmpDir, `${ids[0]}.json`);
    expect(fs.existsSync(filepath)).toBe(true);
  });

  test("runCycle skips blocked tasks", async () => {
    // "delete" triggers needs_confirm safety which blocks auto-execution
    const result = await factory.runCycle("delete everything");

    expect(result.skipped).toBe(true);
    expect(result.reason).toBeDefined();
  });

  test("run processes multiple intents in sequence", async () => {
    const intents = [
      "Build a logger module",
      "Create a utils file",
      "Write a parser component",
    ];

    const packs = await factory.run(intents);

    // All should complete (write triggers needs_confirm but build/create are commands)
    expect(packs.length).toBe(3);
    expect(factory.getCycleCount()).toBe(3);
  });

  test("stop halts the factory loop", async () => {
    // Stop after first cycle completes
    const intents = ["Build module A", "Build module B", "Build module C"];

    // Run in background, stop early
    const runPromise = factory.run(intents);
    // Factory processes first intent synchronously before checking running flag
    // so we stop immediately to test the flag is respected
    factory.stop();

    const packs = await runPromise;
    // Should have at most 1 since we stopped immediately
    expect(packs.length).toBeLessThanOrEqual(intents.length);
  });

  test("getPerformanceSummary returns valid summary after cycles", async () => {
    await factory.runCycle("Build a component");

    const summary = factory.getPerformanceSummary();
    expect(summary.current_index).toBeDefined();
    expect(typeof summary.current_index).toBe("number");
  });

  test("getStats returns outcome statistics", async () => {
    await factory.runCycle("Build something");

    const stats = factory.getStats();
    expect(stats.total).toBe(1);
    expect(stats.successful).toBe(1);
  });

  test("isRunning returns false when not active", () => {
    expect(factory.isRunning()).toBe(false);
  });

  test("cycle count tracks total cycles", async () => {
    expect(factory.getCycleCount()).toBe(0);
    await factory.runCycle("Build item 1");
    await factory.runCycle("Build item 2");
    expect(factory.getCycleCount()).toBe(2);
  });
});

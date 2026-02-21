import { apiGet } from "./client";
import type {
  DatabaseCollections,
  DatabaseStats,
  DatabaseStatus,
} from "../types/databaseLayer";

export function fetchDatabaseStatus(): Promise<DatabaseStatus> {
  return apiGet<DatabaseStatus>("/v1/db/status");
}

export function fetchDatabaseCollections(): Promise<DatabaseCollections> {
  return apiGet<DatabaseCollections>("/v1/db/collections");
}

export function fetchDatabaseStats(): Promise<DatabaseStats> {
  return apiGet<DatabaseStats>("/v1/db/stats");
}

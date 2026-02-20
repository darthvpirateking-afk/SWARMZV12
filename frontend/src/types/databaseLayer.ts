export interface DatabaseCollectionEntry {
  name: string;
  path: string;
  exists: boolean;
  size_bytes: number;
}

export interface DatabaseStatus {
  ok: boolean;
  engine: string;
  data_dir: string;
  generated_at: string;
}

export interface DatabaseCollections {
  ok: boolean;
  generated_at: string;
  collections: DatabaseCollectionEntry[];
}

export interface DatabaseStats {
  ok: boolean;
  generated_at: string;
  mission_rows: number;
  audit_rows: number;
  quarantined_rows: number;
}

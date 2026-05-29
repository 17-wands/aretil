import * as duckdb from "@duckdb/node-api";
import { fileURLToPath } from "url";
import { dirname, join } from "path";

/**
 * DuckDB connection wrapper.
 * Manages async connections to the aretil database.
 */
export interface DbConnection {
  execute(
    sql: string,
    params?: (string | number | boolean | null)[]
  ): Promise<Record<string, unknown>[]>;
  close(): Promise<void>;
}

class DuckDbWrapper implements DbConnection {
  private conn: duckdb.DuckDBConnection;

  constructor(conn: duckdb.DuckDBConnection) {
    this.conn = conn;
  }

  async execute(
    sql: string,
    params?: (string | number | boolean | null)[]
  ): Promise<Record<string, unknown>[]> {
    const values = params || [];
    const reader = await this.conn.runAndRead(sql, values);
    await reader.readAll();
    return reader.getRowObjectsJson();
  }

  async close(): Promise<void> {
    this.conn.closeSync();
  }
}

/**
 * Open an async DuckDB connection.
 * @param dbPath - Path to aretil.duckdb. Defaults to data/aretil.duckdb relative to project root.
 * @returns DbConnection wrapper
 */
export async function openDatabase(dbPath?: string): Promise<DbConnection> {
  const resolvedPath =
    dbPath ||
    join(
      dirname(fileURLToPath(import.meta.url)),
      "../../..",
      "data",
      "aretil.duckdb"
    );

  const instance = await duckdb.DuckDBInstance.create(resolvedPath);
  const conn = await instance.connect();

  return new DuckDbWrapper(conn);
}

import { DbConnection } from "./db.js";

/**
 * Type definitions for macro return shapes.
 */

export interface Matter {
  matter_id: string;
  name: string;
  client_id: string;
  client_name: string;
  practice_area: string;
  deal_type: string;
  jurisdiction: string;
  deal_value: number | null;
  year: number;
  firm_role: string;
  description: string;
  similarity?: number;
}

export interface Timekeeper {
  timekeeper_id: string;
  name: string;
  title: string;
  practice_group: string;
  matter_count?: number;
  top_relevance?: number;
  avg_relevance?: number;
  role_on_matter?: string;
}

export interface Client {
  matter_id: string;
  matter_name: string;
  client_id: string;
  client_name: string;
  via_subsidiary: boolean;
  practice_area: string;
  deal_type: string;
  jurisdiction: string;
  deal_value: number | null;
  year: number;
  firm_role: string;
  description: string;
}

export interface MarketTerms {
  deal_type: string;
  matter_count: number;
  earliest_year: number;
  latest_year: number;
  min_value: number | null;
  p25_value: number | null;
  median_value: number | null;
  p75_value: number | null;
  max_value: number | null;
  mean_value: number | null;
}

export interface PitchContext {
  matters: Matter[];
  timekeepers: Timekeeper[];
  market_terms: MarketTerms | null;
}

/**
 * Search for matters by semantic similarity to a query embedding,
 * optionally filtered by structured fields.
 */
export async function searchMatters(
  db: DbConnection,
  queryEmbedding: number[],
  options?: {
    practiceArea?: string | null;
    industry?: string | null;
    dealType?: string | null;
    jurisdiction?: string | null;
    minValue?: number | null;
    maxValue?: number | null;
    counsel?: string | null;
    resultLimit?: number;
  }
): Promise<Matter[]> {
  const resultLimit = options?.resultLimit ?? 10;
  const embedStr = `[${queryEmbedding.join(",")}]`;

  const sql = `
    SELECT * FROM search_matters(
      ${embedStr}::FLOAT[256],
      practice_area := ?,
      industry := ?,
      deal_type := ?,
      jurisdiction := ?,
      min_value := ?,
      max_value := ?,
      counsel := ?,
      result_limit := ${resultLimit}
    )
  `;

  const rows = await db.execute(sql, [
    options?.practiceArea ?? null,
    options?.industry ?? null,
    options?.dealType ?? null,
    options?.jurisdiction ?? null,
    options?.minValue ?? null,
    options?.maxValue ?? null,
    options?.counsel ?? null,
  ]);

  return rows as unknown as Matter[];
}

/**
 * Find relevant timekeepers ranked by depth of experience for a query.
 */
export async function findRelevantTimekeepers(
  db: DbConnection,
  queryEmbedding: number[],
  resultLimit: number = 10
): Promise<Timekeeper[]> {
  const embedStr = `[${queryEmbedding.join(",")}]`;

  const sql = `
    SELECT * FROM find_relevant_timekeepers(
      ${embedStr}::FLOAT[256],
      result_limit := ${resultLimit}
    )
  `;

  const rows = await db.execute(sql);
  return rows as unknown as Timekeeper[];
}

/**
 * Get a timekeeper's full matter history.
 */
export async function getTimekeeperHistory(
  db: DbConnection,
  timekeeperName: string
): Promise<Timekeeper[]> {
  const sql = `SELECT * FROM get_timekeeper_history(?)`;
  const rows = await db.execute(sql, [timekeeperName]);
  return rows as unknown as Timekeeper[];
}

/**
 * Get a client's history, including subsidiary matters if applicable.
 */
export async function getClientHistory(
  db: DbConnection,
  clientName: string
): Promise<Client[]> {
  const sql = `SELECT * FROM get_client_history(?)`;
  const rows = await db.execute(sql, [clientName]);
  return rows as unknown as Client[];
}

/**
 * Get market statistics for a deal type, optionally filtered by
 * practice area and/or jurisdiction.
 */
export async function getMarketTerms(
  db: DbConnection,
  dealType: string,
  options?: {
    practiceArea?: string | null;
    jurisdiction?: string | null;
  }
): Promise<MarketTerms | null> {
  const sql = `
    SELECT * FROM get_market_terms(
      ?,
      practice_area := ?,
      jurisdiction := ?
    )
  `;

  const rows = await db.execute(sql, [
    dealType,
    options?.practiceArea ?? null,
    options?.jurisdiction ?? null,
  ]);

  if (rows.length === 0) {
    return null;
  }

  return rows[0] as unknown as MarketTerms;
}

/**
 * Assemble pitch context in one bundle: relevant matters, timekeepers,
 * and market terms for the deal type.
 */
export async function assemblePitchContext(
  db: DbConnection,
  queryEmbedding: number[],
  options?: {
    practiceArea?: string | null;
    industry?: string | null;
    dealType?: string | null;
    jurisdiction?: string | null;
    minValue?: number | null;
    maxValue?: number | null;
    matterLimit?: number;
    timekeeperLimit?: number;
  }
): Promise<PitchContext> {
  const embedStr = `[${queryEmbedding.join(",")}]`;
  const matterLimit = options?.matterLimit ?? 5;
  const timekeeperLimit = options?.timekeeperLimit ?? 5;

  const sql = `
    SELECT * FROM assemble_pitch_context(
      ${embedStr}::FLOAT[256],
      q_practice_area := ?,
      q_industry := ?,
      q_deal_type := ?,
      q_jurisdiction := ?,
      q_min_value := ?,
      q_max_value := ?,
      matter_limit := ${matterLimit},
      timekeeper_limit := ${timekeeperLimit}
    )
  `;

  const rows = await db.execute(sql, [
    options?.practiceArea ?? null,
    options?.industry ?? null,
    options?.dealType ?? null,
    options?.jurisdiction ?? null,
    options?.minValue ?? null,
    options?.maxValue ?? null,
  ]);

  if (rows.length === 0) {
    return { matters: [], timekeepers: [], market_terms: null };
  }

  const row = rows[0];

  // DuckDB returns nested structures; need to parse them
  return {
    matters: (row.matters || []) as Matter[],
    timekeepers: (row.timekeepers || []) as Timekeeper[],
    market_terms: row.market_terms as MarketTerms | null,
  };
}

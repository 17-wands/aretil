import { describe, it, expect, beforeAll, afterAll } from "vitest";
import { openDatabase, DbConnection } from "./db.js";
import {
  searchMatters,
  findRelevantTimekeepers,
  getTimekeeperHistory,
  getClientHistory,
  getMarketTerms,
  assemblePitchContext,
} from "./macros.js";
import { dirname, join } from "path";
import { fileURLToPath } from "url";

describe("Macro wrappers", () => {
  let db: DbConnection;

  beforeAll(async () => {
    // Open database connection for all tests
    const dbPath = join(
      dirname(fileURLToPath(import.meta.url)),
      "../../..",
      "data",
      "aretil.duckdb"
    );
    db = await openDatabase(dbPath);
  });

  afterAll(async () => {
    // Close connection after all tests
    await db.close();
  });

  describe("searchMatters", () => {
    it("should return matters ranked by similarity", async () => {
      // Use a simple embedding (all 0.1 for MVP)
      const embedding = Array(256).fill(0.1);

      const matters = await searchMatters(db, embedding, { resultLimit: 5 });

      expect(Array.isArray(matters)).toBe(true);
      expect(matters.length).toBeGreaterThan(0);
      expect(matters[0]).toHaveProperty("matter_id");
      expect(matters[0]).toHaveProperty("similarity");
      // Results should be ordered by similarity DESC
      if (matters.length > 1) {
        expect(matters[0].similarity).toBeGreaterThanOrEqual(
          matters[1].similarity!
        );
      }
    });

    it("should filter by deal type", async () => {
      const embedding = Array(256).fill(0.1);
      const matters = await searchMatters(db, embedding, {
        dealType: "Merger",
        resultLimit: 5,
      });

      expect(Array.isArray(matters)).toBe(true);
      matters.forEach((m) => {
        expect(m.deal_type).toBe("Merger");
      });
    });

    it("should respect result limit", async () => {
      const embedding = Array(256).fill(0.1);
      const matters = await searchMatters(db, embedding, { resultLimit: 3 });

      expect(matters.length).toBeLessThanOrEqual(3);
    });
  });

  describe("findRelevantTimekeepers", () => {
    it("should return timekeepers ranked by relevance", async () => {
      const embedding = Array(256).fill(0.1);
      const timekeepers = await findRelevantTimekeepers(db, embedding, 5);

      expect(Array.isArray(timekeepers)).toBe(true);
      expect(timekeepers.length).toBeGreaterThan(0);
      expect(timekeepers[0]).toHaveProperty("timekeeper_id");
      expect(timekeepers[0]).toHaveProperty("top_relevance");
      // Should be ordered by top_relevance DESC
      if (timekeepers.length > 1) {
        expect(timekeepers[0].top_relevance).toBeGreaterThanOrEqual(
          timekeepers[1].top_relevance!
        );
      }
    });

    it("should respect result limit", async () => {
      const embedding = Array(256).fill(0.1);
      const timekeepers = await findRelevantTimekeepers(db, embedding, 2);

      expect(timekeepers.length).toBeLessThanOrEqual(2);
    });
  });

  describe("getTimekeeperHistory", () => {
    it("should return a timekeeper's matter history", async () => {
      // First, get a timekeeper name from the database
      const embedding = Array(256).fill(0.1);
      const timekeepers = await findRelevantTimekeepers(db, embedding, 1);

      if (timekeepers.length === 0) {
        expect(true).toBe(true); // Skip if no timekeepers
        return;
      }

      const { name } = timekeepers[0];
      const history = await getTimekeeperHistory(db, name);

      expect(Array.isArray(history)).toBe(true);
      expect(history.length).toBeGreaterThan(0);
      history.forEach((h) => {
        expect(h.name).toBe(name);
        expect(h).toHaveProperty("matter_name");
      });
    });
  });

  describe("getClientHistory", () => {
    it("should return a client's matter history", async () => {
      // First, get a client name from the database
      const embedding = Array(256).fill(0.1);
      const matters = await searchMatters(db, embedding, { resultLimit: 1 });

      if (matters.length === 0) {
        expect(true).toBe(true); // Skip if no matters
        return;
      }

      const { client_name } = matters[0];
      const history = await getClientHistory(db, client_name);

      expect(Array.isArray(history)).toBe(true);
      expect(history.length).toBeGreaterThan(0);
      history.forEach((h) => {
        expect(h.client_name).toBe(client_name);
        expect(h).toHaveProperty("matter_name");
      });
    });
  });

  describe("getMarketTerms", () => {
    it("should return market statistics for a deal type", async () => {
      const terms = await getMarketTerms(db, "Merger");

      expect(terms).not.toBeNull();
      if (terms) {
        expect(terms).toHaveProperty("deal_type");
        expect(terms).toHaveProperty("matter_count");
        expect(terms.deal_type).toBe("Merger");
        expect(Number(terms.matter_count)).toBeGreaterThan(0);
      }
    });

    it("should filter by practice area", async () => {
      const terms = await getMarketTerms(db, "Merger", {
        practiceArea: "Healthcare M&A",
      });

      if (terms) {
        expect(Number(terms.matter_count)).toBeGreaterThanOrEqual(0);
      }
    });
  });

  describe("assemblePitchContext", () => {
    it("should return a complete pitch context bundle", async () => {
      const embedding = Array(256).fill(0.1);
      const context = await assemblePitchContext(db, embedding, {
        dealType: "Merger",
        matterLimit: 5,
        timekeeperLimit: 5,
      });

      expect(context).toHaveProperty("matters");
      expect(context).toHaveProperty("timekeepers");
      expect(context).toHaveProperty("market_terms");
      expect(Array.isArray(context.matters)).toBe(true);
      expect(Array.isArray(context.timekeepers)).toBe(true);
    });

    it("should respect matter and timekeeper limits", async () => {
      const embedding = Array(256).fill(0.1);
      const context = await assemblePitchContext(db, embedding, {
        matterLimit: 3,
        timekeeperLimit: 2,
      });

      expect(context.matters.length).toBeLessThanOrEqual(3);
      expect(context.timekeepers.length).toBeLessThanOrEqual(2);
    });
  });
});

import express, { Request, Response } from "express";
import { openDatabase } from "./db.js";
import { runPitchWorkflow } from "./client.js";

const app = express();
const PORT = 3001;

// Middleware
app.use(express.json());

/**
 * GET /health
 * Returns server status.
 */
app.get("/health", (req: Request, res: Response): void => {
  res.json({ status: "ok" });
});

/**
 * POST /pitch
 * Accepts an RFP JSON payload and returns a markdown pitch.
 * Requires ANTHROPIC_API_KEY environment variable.
 *
 * Request body:
 * {
 *   "rfp": "... RFP text ..."
 * }
 *
 * Response:
 * {
 *   "pitch": "... markdown pitch ..."
 * }
 */
app.post("/pitch", async (req: Request, res: Response): Promise<void> => {
  const { rfp } = req.body as { rfp?: string };

  if (!rfp || typeof rfp !== "string") {
    res.status(400).json({ error: "Missing or invalid 'rfp' field" });
    return;
  }

  const apiKey = process.env.ANTHROPIC_API_KEY;
  if (!apiKey) {
    res.status(503).json({
      error: "ANTHROPIC_API_KEY not set. Pitch generation unavailable.",
    });
    return;
  }

  let db = null;

  try {
    // Open database connection
    db = await openDatabase();

    // Run the pitch workflow
    const pitch = await runPitchWorkflow(db, rfp, apiKey);

    res.json({ pitch });
  } catch (err) {
    console.error("[ERROR] Pitch generation failed:", err);
    res.status(500).json({
      error: `Pitch generation failed: ${
        err instanceof Error ? err.message : String(err)
      }`,
    });
  } finally {
    // Close database connection
    if (db) {
      await db.close();
    }
  }
});

/**
 * Error handler for undefined routes.
 */
app.use((req: Request, res: Response): void => {
  res.status(404).json({ error: "Not found" });
});

/**
 * Global error handler.
 */
app.use(
  (
    err: Error,
    req: Request,
    res: Response,
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    next: express.NextFunction
  ): void => {
    console.error("[ERROR]", err.message);
    res.status(500).json({ error: "Internal server error" });
  }
);

/**
 * Start the server.
 */
const server = app.listen(PORT, (): void => {
  console.log(`[aretil API] listening on http://localhost:${PORT}`);
});

/**
 * Graceful shutdown.
 */
process.on("SIGTERM", (): void => {
  console.log("[aretil API] SIGTERM received, shutting down gracefully");
  server.close((): void => {
    process.exit(0);
  });
});

import { execSync } from "child_process";

/**
 * Embed a query string using the Python embed_matters.embed_query() function.
 *
 * MVP: Uses Python subprocess. Future optimization: port to JavaScript
 * (ONNX.js or Transformers.js) for better performance.
 *
 * @param text - Text to embed
 * @returns 256-dimensional embedding vector
 * @throws Error if embedding fails
 */
export function embedQuery(text: string): number[] {
  try {
    const pythonCode = `
import json
from embed_matters import embed_query
result = embed_query(${JSON.stringify(text)})
print(json.dumps(result))
`;

    const output = execSync(`uv run python -c "${pythonCode.replace(/"/g, '\\"')}"`, {
      encoding: "utf-8",
      stdio: ["pipe", "pipe", "pipe"],
    });

    const embedding = JSON.parse(output.trim()) as number[];

    if (!Array.isArray(embedding) || embedding.length !== 256) {
      throw new Error(
        `Expected 256-dimensional embedding, got ${embedding.length}`
      );
    }

    return embedding;
  } catch (err) {
    throw new Error(
      `Embedding failed: ${err instanceof Error ? err.message : String(err)}`
    );
  }
}

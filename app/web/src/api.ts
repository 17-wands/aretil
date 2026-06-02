/**
 * API client for the aretil Node server.
 * Provides typed wrappers around HTTP endpoints.
 */

export interface PitchResponse {
  pitch: string;
}

export interface HealthResponse {
  status: string;
}

const API_BASE = "/api";

/**
 * Check server health.
 */
export async function checkHealth(): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE}/health`);
  if (!response.ok) {
    throw new Error(`Health check failed: ${response.statusText}`);
  }
  return response.json();
}

/**
 * Request a pitch for an RFP.
 * @param rfp - The RFP text
 * @returns The drafted pitch in markdown
 */
export async function requestPitch(rfp: string): Promise<string> {
  const response = await fetch(`${API_BASE}/pitch`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ rfp }),
  });

  if (!response.ok) {
    const errorText = await response.text();
    throw new Error(`Pitch generation failed: ${response.statusText} — ${errorText}`);
  }

  const data: PitchResponse = await response.json();
  return data.pitch;
}

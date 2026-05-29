import { Tool } from "@anthropic-ai/sdk/resources/messages.js";

/**
 * Tool definitions for Claude.
 * Each tool mirrors a SQL macro in the aretil database.
 */

export const tools: Tool[] = [
  {
    name: "search_matters",
    description:
      "Search for matters by semantic similarity to a query embedding, optionally filtered by practice area, industry, deal type, jurisdiction, and deal value range.",
    input_schema: {
      type: "object" as const,
      properties: {
        query_embedding: {
          type: "array",
          items: { type: "number" },
          minItems: 256,
          maxItems: 256,
          description:
            "256-dimensional embedding vector of the search query intent.",
        },
        practice_area: {
          type: ["string", "null"],
          description:
            "Optional: filter by practice area (e.g., 'Healthcare M&A').",
        },
        industry: {
          type: ["string", "null"],
          description: "Optional: filter by client industry.",
        },
        deal_type: {
          type: ["string", "null"],
          description: "Optional: filter by deal type (e.g., 'Merger').",
        },
        jurisdiction: {
          type: ["string", "null"],
          description: "Optional: filter by jurisdiction (e.g., 'California').",
        },
        min_value: {
          type: ["number", "null"],
          description: "Optional: minimum deal value.",
        },
        max_value: {
          type: ["number", "null"],
          description: "Optional: maximum deal value.",
        },
        result_limit: {
          type: "number",
          description: "Number of results to return (default: 10).",
          default: 10,
        },
      },
      required: ["query_embedding"],
    },
  },
  {
    name: "find_relevant_timekeepers",
    description:
      "Find timekeepers ranked by depth of relevant matter experience for a query embedding.",
    input_schema: {
      type: "object" as const,
      properties: {
        query_embedding: {
          type: "array",
          items: { type: "number" },
          minItems: 256,
          maxItems: 256,
          description: "256-dimensional embedding vector of the search query.",
        },
        result_limit: {
          type: "number",
          description: "Number of timekeepers to return (default: 10).",
          default: 10,
        },
      },
      required: ["query_embedding"],
    },
  },
  {
    name: "get_timekeeper_history",
    description:
      "Get a timekeeper's full matter history including their roles on each matter.",
    input_schema: {
      type: "object" as const,
      properties: {
        timekeeper_name: {
          type: "string",
          description: "The timekeeper's name.",
        },
      },
      required: ["timekeeper_name"],
    },
  },
  {
    name: "get_client_history",
    description:
      "Get a client's matter history, including subsidiary matters if applicable.",
    input_schema: {
      type: "object" as const,
      properties: {
        client_name: {
          type: "string",
          description: "The client name.",
        },
      },
      required: ["client_name"],
    },
  },
  {
    name: "get_market_terms",
    description:
      "Get aggregate market statistics for a deal type, optionally filtered by practice area and jurisdiction.",
    input_schema: {
      type: "object" as const,
      properties: {
        deal_type: {
          type: "string",
          description: "The deal type (e.g., 'Merger', 'Acquisition').",
        },
        practice_area: {
          type: ["string", "null"],
          description: "Optional: filter by practice area.",
        },
        jurisdiction: {
          type: ["string", "null"],
          description: "Optional: filter by jurisdiction.",
        },
      },
      required: ["deal_type"],
    },
  },
  {
    name: "assemble_pitch_context",
    description:
      "Assemble a complete pitch context bundle: relevant matters, top timekeepers, and market statistics in a single call.",
    input_schema: {
      type: "object" as const,
      properties: {
        query_embedding: {
          type: "array",
          items: { type: "number" },
          minItems: 256,
          maxItems: 256,
          description: "256-dimensional embedding vector of the RFP intent.",
        },
        practice_area: {
          type: ["string", "null"],
          description: "Optional: filter by practice area.",
        },
        industry: {
          type: ["string", "null"],
          description: "Optional: filter by industry.",
        },
        deal_type: {
          type: ["string", "null"],
          description: "Optional: filter by deal type.",
        },
        jurisdiction: {
          type: ["string", "null"],
          description: "Optional: filter by jurisdiction.",
        },
        min_value: {
          type: ["number", "null"],
          description: "Optional: minimum deal value.",
        },
        max_value: {
          type: ["number", "null"],
          description: "Optional: maximum deal value.",
        },
        matter_limit: {
          type: "number",
          description: "Number of matters to return (default: 5).",
          default: 5,
        },
        timekeeper_limit: {
          type: "number",
          description: "Number of timekeepers to return (default: 5).",
          default: 5,
        },
      },
      required: ["query_embedding"],
    },
  },
];

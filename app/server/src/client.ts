import Anthropic from "@anthropic-ai/sdk";
import { DbConnection } from "./db.js";
import * as macros from "./macros.js";
import { embedQuery } from "./embed.js";
import { tools } from "./tools.js";

interface ToolInput {
  [key: string]: unknown;
}

/**
 * Run the pitch workflow: parse RFP, call Claude with tool-use loop,
 * execute macro tool calls, and return the final pitch markdown.
 */
export async function runPitchWorkflow(
  db: DbConnection,
  rfp: string,
  apiKey: string
): Promise<string> {
  const client = new Anthropic({ apiKey });

  const pitchPrompt = `You are a legal business-development specialist drafting a response pitch from an inbound RFP.

Your task:
1. Parse the RFP into structured query intent (practice area, deal type, industry, jurisdiction, deal value).
2. Call assemble_pitch_context to fetch relevant matters, timekeepers, and market statistics.
3. Draft a pitch in markdown that includes:
   - Firm positioning paragraph
   - Relevant past experience (3-5 matters)
   - Team section with 2-3 key timekeepers
   - Why us paragraph
   - Closing commitment

Output only markdown. No prose outside the markdown block.`;

  const messages: Anthropic.Messages.MessageParam[] = [
    {
      role: "user",
      content: `Please draft a pitch in response to this RFP:\n\n${rfp}`,
    },
  ];

  let finalPitch: string | null = null;
  let iteration = 0;
  const maxIterations = 10;

  while (iteration < maxIterations) {
    iteration++;

    // Call Claude with tool definitions
    const response = await client.messages.create({
      model: "claude-opus-4-7",
      max_tokens: 4096,
      system: pitchPrompt,
      tools: tools,
      messages: messages,
    });

    // Check stop reason
    if (response.stop_reason === "end_turn") {
      // Extract final pitch from response
      for (const block of response.content) {
        if (block.type === "text") {
          finalPitch = block.text;
          break;
        }
      }
      break;
    }

    if (response.stop_reason === "tool_use") {
      // Process tool calls
      const toolUseBlocks = response.content.filter(
        (block) => block.type === "tool_use"
      );

      // Add assistant's response to messages
      messages.push({
        role: "assistant",
        content: response.content,
      });

      // Process each tool call and collect results
      const toolResults: Anthropic.Messages.ToolResultBlockParam[] = [];

      for (const toolUse of toolUseBlocks) {
        if (toolUse.type !== "tool_use") continue;

        const toolName = toolUse.name;
        const toolInput = toolUse.input as ToolInput;

        let toolResult: unknown;
        let errorMessage: string | null = null;

        try {
          // Execute the appropriate macro
          if (toolName === "search_matters") {
            const embedding = (toolInput.query_embedding as number[]) || [];
            toolResult = await macros.searchMatters(db, embedding, {
              practiceArea: toolInput.practice_area as string | null,
              industry: toolInput.industry as string | null,
              dealType: toolInput.deal_type as string | null,
              jurisdiction: toolInput.jurisdiction as string | null,
              minValue: toolInput.min_value as number | null,
              maxValue: toolInput.max_value as number | null,
              resultLimit: (toolInput.result_limit as number) || 10,
            });
          } else if (toolName === "find_relevant_timekeepers") {
            const embedding = (toolInput.query_embedding as number[]) || [];
            toolResult = await macros.findRelevantTimekeepers(
              db,
              embedding,
              (toolInput.result_limit as number) || 10
            );
          } else if (toolName === "get_timekeeper_history") {
            const name = toolInput.timekeeper_name as string;
            toolResult = await macros.getTimekeeperHistory(db, name);
          } else if (toolName === "get_client_history") {
            const name = toolInput.client_name as string;
            toolResult = await macros.getClientHistory(db, name);
          } else if (toolName === "get_market_terms") {
            const dealType = toolInput.deal_type as string;
            toolResult = await macros.getMarketTerms(db, dealType, {
              practiceArea: toolInput.practice_area as string | null,
              jurisdiction: toolInput.jurisdiction as string | null,
            });
          } else if (toolName === "assemble_pitch_context") {
            const embedding = (toolInput.query_embedding as number[]) || [];
            toolResult = await macros.assemblePitchContext(db, embedding, {
              practiceArea: toolInput.practice_area as string | null,
              industry: toolInput.industry as string | null,
              dealType: toolInput.deal_type as string | null,
              jurisdiction: toolInput.jurisdiction as string | null,
              minValue: toolInput.min_value as number | null,
              maxValue: toolInput.max_value as number | null,
              matterLimit: (toolInput.matter_limit as number) || 5,
              timekeeperLimit: (toolInput.timekeeper_limit as number) || 5,
            });
          } else {
            errorMessage = `Unknown tool: ${toolName}`;
            toolResult = null;
          }
        } catch (err) {
          errorMessage = `Tool execution error: ${
            err instanceof Error ? err.message : String(err)
          }`;
          toolResult = null;
        }

        toolResults.push({
          type: "tool_result",
          tool_use_id: toolUse.id,
          content: errorMessage || JSON.stringify(toolResult),
        });
      }

      // Add tool results to messages
      messages.push({
        role: "user",
        content: toolResults,
      });
    } else {
      // Unexpected stop reason
      break;
    }
  }

  if (!finalPitch) {
    throw new Error("Claude did not produce a pitch output");
  }

  return finalPitch;
}

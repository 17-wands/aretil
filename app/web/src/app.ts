/**
 * Main app component — RFP input and pitch display.
 */

import { requestPitch } from "./api.js";

/**
 * Safely retrieve and validate a DOM element with type checking.
 */
function getElementOrThrow<T extends HTMLElement>(id: string): T {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Required element not found: id="${id}"`);
  }
  return element as T;
}

/**
 * Initialize and render the app.
 */
export function initializeApp(): void {
  const appDiv = document.getElementById("app");
  if (!appDiv) {
    console.error("App container not found");
    return;
  }

  appDiv.innerHTML = `
    <div class="app-container">
      <header>
        <h1>aretil</h1>
        <p style="color: var(--ds-gunmetal); margin-bottom: var(--ds-spacing-24);">
          Pitch drafting from your firm's experience.
        </p>
      </header>

      <div class="app-split">
        <div class="app-split-panel">
          <h2>RFP</h2>
          <div class="card">
            <div class="card-header">Request for Proposal</div>
            <div class="card-content">
              <textarea
                id="rfp-input"
                placeholder="Paste an RFP here. aretil will search your firm's experience and draft a response."
              ></textarea>
            </div>
            <div class="card-footer">
              <button id="submit-btn" class="btn-primary">
                Generate pitch
              </button>
            </div>
          </div>
        </div>

        <div class="app-split-panel">
          <h2>Pitch</h2>
          <div class="card" style="display: flex; flex-direction: column;">
            <div id="status-message"></div>
            <div id="pitch-content" class="card-content" style="flex: 1;">
              <p style="color: var(--ds-gunmetal); text-align: center; padding: var(--ds-spacing-40) 0;">
                Your pitch will appear here.
              </p>
            </div>
            <div class="card-footer">
              <button id="copy-btn" class="btn-secondary" style="display: none;">
                Copy to clipboard
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  `;

  // Wire up event handlers with validated DOM retrieval
  const rfpInput = getElementOrThrow<HTMLTextAreaElement>("rfp-input");
  const submitBtn = getElementOrThrow<HTMLButtonElement>("submit-btn");
  const pitchContent = getElementOrThrow<HTMLDivElement>("pitch-content");
  const statusMessage = getElementOrThrow<HTMLDivElement>("status-message");
  const copyBtn = getElementOrThrow<HTMLButtonElement>("copy-btn");

  let currentPitch = "";

  submitBtn.addEventListener("click", async () => {
    const rfp = rfpInput.value.trim();

    if (!rfp) {
      statusMessage.innerHTML =
        '<div class="error">Please paste an RFP above.</div>';
      return;
    }

    // Show loading state
    submitBtn.disabled = true;
    statusMessage.innerHTML = `
      <div style="display: flex; align-items: center; gap: var(--ds-spacing-8); color: var(--ds-warning-amber);">
        <span class="spinner"></span>
        <span>Generating pitch…</span>
      </div>
    `;
    pitchContent.innerHTML = "";
    copyBtn.style.display = "none";

    try {
      const pitch = await requestPitch(rfp);
      currentPitch = pitch;

      // Render pitch as markdown-style HTML
      pitchContent.innerHTML = `<div class="markdown">${renderMarkdown(pitch)}</div>`;
      statusMessage.innerHTML = `<div class="success">✓ Pitch generated</div>`;
      copyBtn.style.display = "inline-block";
    } catch (error) {
      const message = error instanceof Error ? error.message : "Unknown error";
      statusMessage.innerHTML = `<div class="error">Error: ${message}</div>`;
      pitchContent.innerHTML = "";
      copyBtn.style.display = "none";
    } finally {
      submitBtn.disabled = false;
    }
  });

  copyBtn.addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(currentPitch);
      statusMessage.innerHTML = `<div class="success">✓ Copied to clipboard</div>`;
      setTimeout(() => {
        statusMessage.innerHTML = `<div class="success">✓ Pitch generated</div>`;
      }, 2000);
    } catch (error) {
      statusMessage.innerHTML = `<div class="error">Failed to copy</div>`;
    }
  });

  // Allow Enter + Cmd/Ctrl to submit
  rfpInput.addEventListener("keydown", (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
      submitBtn.click();
    }
  });
}

/**
 * Simple markdown-to-HTML converter.
 * Handles basic markdown: headings, paragraphs, bold, italic, code.
 * Note: List support removed due to regex edge cases; consider marked.js for production.
 */
function renderMarkdown(markdown: string): string {
  // Escape HTML entities first (must precede pattern replacements)
  const escaped = markdown
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Convert markdown patterns to HTML
  const withMarkdown = escaped
    .replace(/^### (.*?)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*?)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*?)$/gm, "<h1>$1</h1>")
    .replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/__(.+?)__/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/_(.+?)_/g, "<em>$1</em>");

  // Wrap paragraphs (skip already-wrapped content)
  const html = withMarkdown
    .split("\n\n")
    .map((para) => para.match(/^<[hou]/) ? para : `<p>${para.replace(/\n/g, "<br>")}</p>`)
    .join("\n");

  return html;
}

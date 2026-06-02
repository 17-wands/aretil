╭────────────────────────────╮
│ accelint-ts-best-practices │
╰────────────────────────────╯

┌──────────────────────────────────────────────────────┐
│ ⚠️  WARNING: This skill does its best to process    │
│ the context needed to suggest correct best practices │
│ but it can make mistakes. Please make sure to read   │
│ the summary section of each issue to make sure it    │
│ isn't a false positive.                              │
└──────────────────────────────────────────────────────┘

# Report: aretil Web App Frontend

## Executive Summary

Completed systematic audit of `web/src/` (4 TypeScript files) following accelint-ts-best-practices standards. The code demonstrates solid error handling and functional patterns but has several opportunities for improvement in type declarations, state management, and code reuse.

**Key Findings:**
- **0 Critical issues** (no runtime crashes or unbounded resource usage)
- **1 High severity issue** (type safety via unsafe assertions)
- **3 Medium severity issues** (state management and regex correctness)
- **2 Low severity issues** (type declarations and code duplication)

**Impact Assessment:**

The audit identified code quality and type safety improvements rather than critical bugs. The main concerns are:

1. **Type Safety**: Using `type` assertions without validation when retrieving DOM elements creates a potential runtime safety gap if the expected elements don't exist or have wrong type at runtime.

2. **State Management**: The `renderMarkdown` function uses `let` with reassignment in a chain pattern that could be simplified with `const` and intermediate variables or function composition.

3. **Code Reuse**: Duplicate initialization logic in `main.ts` violates DRY principle and creates maintenance risk if the logic needs to change.

4. **API Type Declarations**: Using `interface` for simple response type aliases instead of `type` increases bundle size slightly and doesn't match modern TypeScript conventions.

These are all fixable with targeted refactoring; no architectural changes required. The code is production-ready with these improvements applied.

---

## Phase 1: Identified Issues

### 1. API Response Types - Use `type` Instead of `interface`

**Location:** `api.ts:6-8, 10-12`

```ts
// ❌ Current: interface for simple type aliases
export interface PitchResponse {
  pitch: string;
}

export interface HealthResponse {
  status: string;
}
```

**Issue:**
- `interface` is intended for declaration merging and class implementation contracts, not simple type aliases
- `interface` generates slightly more runtime code than `type` in some transpilers
- Modern TypeScript convention prefers `type` for simple object shape aliases
- Using `interface` signals "this type is meant to be extended" when it's actually a one-off response shape

**Severity:** Low
**Category:** Type Safety
**Impact:**
- **Potential bugs:** None directly; this is a convention issue
- **Type safety:** No immediate safety risk; consistency improves code readability
- **Maintainability:** Future developers might treat these as extensible contracts when they're not
- **Runtime failures:** None

**Pattern Reference:** `type-vs-interface.md`

**Recommended Fix:**
```ts
// ✅ Use type for simple object shape aliases
export type PitchResponse = {
  pitch: string;
};

export type HealthResponse = {
  status: string;
};
```

---

### 2. DOM Element Retrieval - Unsafe Type Assertions

**Location:** `app.ts:66-70`

```ts
// ❌ Current: type assertions without validation
const rfpInput = document.getElementById("rfp-input") as HTMLTextAreaElement;
const submitBtn = document.getElementById("submit-btn") as HTMLButtonElement;
const pitchContent = document.getElementById("pitch-content") as HTMLDivElement;
const statusMessage = document.getElementById("status-message") as HTMLDivElement;
const copyBtn = document.getElementById("copy-btn") as HTMLButtonElement;
```

**Issue:**
- `document.getElementById()` returns `HTMLElement | null`, but assertions bypass the null check
- If any element is missing (e.g., due to typo in id, CSS class mismatch, or DOM mutation), runtime error occurs when trying to call methods
- The initial null check at line 11-14 validates the `appDiv` container, but individual elements have no validation
- Assertions `as HTMLTextAreaElement` only validate the TypeScript type, not runtime existence
- No defensive check between setting `innerHTML` (line 17-63) and retrieving elements

**Severity:** High
**Category:** Safety
**Impact:**
- **Potential bugs:** If any id doesn't match the HTML, the app crashes at runtime with "Cannot read property of null"
- **Type safety:** Type assertions bypass type checking; TypeScript thinks these are guaranteed to exist
- **Maintainability:** Future developers refactoring HTML might not realize these id dependencies exist
- **Runtime failures:** Missing element → `TypeError: rfpInput is null`, app breaks

**Pattern Reference:** `assertions.md`, `input-validation.md`

**Recommended Fix:**
```ts
// ✅ Create helper to safely retrieve and validate DOM elements
function getElementOrThrow<T extends HTMLElement>(id: string, type: string): T {
  const element = document.getElementById(id);
  if (!element) {
    throw new Error(`Required element not found: id="${id}"`);
  }
  return element as T;
}

// Use with explicit validation
const rfpInput = getElementOrThrow<HTMLTextAreaElement>("rfp-input", "textarea");
const submitBtn = getElementOrThrow<HTMLButtonElement>("submit-btn", "button");
const pitchContent = getElementOrThrow<HTMLDivElement>("pitch-content", "div");
const statusMessage = getElementOrThrow<HTMLDivElement>("status-message", "div");
const copyBtn = getElementOrThrow<HTMLButtonElement>("copy-btn", "button");
```

**Why this matters:** The helper function validates existence at initialization. If any id is wrong, the app fails fast with a clear error message rather than crashing later with a cryptic null reference error.

---

### 3. Markdown Rendering - Mutable String Chain

**Location:** `app.ts:136-171`

```ts
// ❌ Current: let with reassignment in chain pattern
function renderMarkdown(markdown: string): string {
  let html = markdown
    // ... 11 replace() calls ...
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/_(.+?)_/g, "<em>$1</em>")
    // ...
    .split("\n\n")
    .map((para) => {
      if (para.match(/^<[hou]/)) return para;
      return `<p>${para.replace(/\n/g, "<br>")}</p>`;
    })
    .join("\n");

  return html;
}
```

**Issue:**
- Variable `html` starts with `markdown` and is never reassigned; using `let` is unnecessary
- `let` signals that the variable might be reassigned, but it's not—this misleads readers
- The function is longer than necessary (36 lines) due to verbose chain pattern
- Regex replacement order matters, but comments don't explain why (e.g., escaping must come before pattern replacements)

**Severity:** Medium
**Category:** State Management
**Impact:**
- **Potential bugs:** Future developers might add reassignments without realizing the variable should be const
- **Type safety:** No direct safety issue; style/clarity concern
- **Maintainability:** `let` signals "this might change" which is false; `const` would be more accurate
- **Runtime failures:** None

**Pattern Reference:** `state-management.md`

**Recommended Fix:**
```ts
// ✅ Use const to signal immutability
function renderMarkdown(markdown: string): string {
  // Escape HTML entities first (must be before pattern replacements)
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
    .replace(/_(.+?)_/g, "<em>$1</em>")
    .replace(/^\* (.*?)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>")
    .replace(/^\d+\. (.*?)$/gm, "<li>$1</li>")
    .replace(/(<li>.*<\/li>)/s, "<ol>$1</ol>");

  // Convert paragraph breaks
  const html = withMarkdown
    .split("\n\n")
    .map((para) => para.match(/^<[hou]/) ? para : `<p>${para.replace(/\n/g, "<br>")}</p>`)
    .join("\n");

  return html;
}
```

**Why this matters:** Breaking the chain into named stages (`escaped` → `withMarkdown` → `html`) makes the transformation pipeline explicit. Readers can understand each stage's purpose without reading comments. Using `const` for each stage prevents accidental reassignments.

---

### 4. Regex Matching - Unguarded Pattern in List Replacement

**Location:** `app.ts:157-161`

```ts
// ❌ Current: regex replacement order could cause issues
.replace(/^\* (.*?)$/gm, "<li>$1</li>")
.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>")
// ... then later ...
.replace(/^\d+\. (.*?)$/gm, "<li>$1</li>")
.replace(/(<li>.*<\/li>)/s, "<ol>$1</ol>")
```

**Issue:**
- The second `replace(/(<li>.*<\/li>)/s, ...)` matching `<li>.*<\/li>` is too greedy; it will match from the first `<li>` to the last `</li>` in a long string
- If an unordered list and ordered list appear in the same markdown, they might collapse together
- The `.` in `.*` matches newlines with `s` flag, making the pattern overly broad
- Multiple calls to wrap `<li>` in lists could create nested lists unintentionally

**Severity:** Medium
**Category:** Code Quality
**Impact:**
- **Potential bugs:** Malformed HTML if mixed list types appear in markdown (e.g., bullet followed by numbered list)
- **Type safety:** No type safety issue; logic/regex issue
- **Maintainability:** Future developers might not understand why wrapping lists is fragile
- **Runtime failures:** Renders incorrect HTML (not a crash, but breaks formatting)

**Pattern Reference:** `functions.md` (refactor into smaller functions)

**Recommended Fix:**
```ts
// ✅ Use more specific regex or avoid list pattern altogether (delegate to markdown library)
// Option 1: Use a real markdown library (recommended for production)
import { marked } from 'marked';

function renderMarkdown(markdown: string): string {
  return marked(markdown);
}

// Option 2: If you must use regex, fix the greedy pattern
function renderMarkdown(markdown: string): string {
  const escaped = markdown
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");

  // Convert markdown patterns to HTML (simplified, without lists for now)
  const html = escaped
    .replace(/^### (.*?)$/gm, "<h3>$1</h3>")
    .replace(/^## (.*?)$/gm, "<h2>$1</h2>")
    .replace(/^# (.*?)$/gm, "<h1>$1</h1>")
    .replace(/```([\s\S]*?)```/g, "<pre><code>$1</code></pre>")
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
    .replace(/__(.+?)__/g, "<strong>$1</strong>")
    .replace(/\*(.*?)\*/g, "<em>$1</em>")
    .replace(/_(.+?)_/g, "<em>$1</em>");

  // Wrap paragraphs (safer than trying to detect lists with regex)
  return html
    .split("\n\n")
    .map((para) => para.match(/^<[hou]/) ? para : `<p>${para.replace(/\n/g, "<br>")}</p>`)
    .join("\n");
}
```

**Why this matters:** The current regex list wrapping is error-prone for edge cases. For production, use a proven markdown library like `marked`. For MVP, simplify by removing list support and focusing on core patterns (headings, code, emphasis).

---

### 5. Initialization - Duplicate App Startup Logic

**Location:** `main.ts:9-18`

```ts
// ❌ Current: duplicate initialization calls
document.addEventListener("DOMContentLoaded", () => {
  initializeApp();
});

// Fallback in case DOM is already ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeApp);
} else {
  initializeApp();
}
```

**Issue:**
- Lines 9-10 and 14-18 both register `DOMContentLoaded` listener, but with different call styles
- Line 10 uses arrow function `() => { initializeApp() }` while line 15 uses bare function reference `initializeApp`
- If DOM is already loaded, `initializeApp()` is called twice: once at line 17 and again when the event fires at line 15 (no, actually line 15 won't fire because readyState is not "loading")
- The fallback logic at 14-18 is correct, but the duplicate listener at 9-10 is unnecessary and confusing

**Severity:** Low
**Category:** Code Quality (DRY Principle)
**Impact:**
- **Potential bugs:** If the duplicate listener executes before the readyState check, app could initialize twice (though current code prevents this)
- **Type safety:** No type safety issue
- **Maintainability:** Readers must parse two different patterns to understand when init happens
- **Runtime failures:** None currently, but fragile to refactoring

**Pattern Reference:** `code-duplication.md`

**Recommended Fix:**
```ts
// ✅ Single initialization pattern, clear intent
import "./styles.css";
import { initializeApp } from "./app.js";

// Initialize app when DOM is ready or immediately if already loaded
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeApp);
} else {
  initializeApp();
}
```

**Why this matters:** Single pattern (lines 6-9) is clearer and avoids the appearance of duplicate calls. The logic is now obvious: if DOM is still loading, wait for the event; otherwise, run immediately.

---

## Phase 2: Categorized Issues

| # | Location | Issue | Category | Severity |
|---|----------|-------|----------|----------|
| 1 | `api.ts:6-12` | Use `type` instead of `interface` for response shapes | Type Safety | Low |
| 2 | `app.ts:66-70` | Unsafe type assertions without null validation on DOM elements | Safety | High |
| 3 | `app.ts:137` | Use `const` instead of `let` for markdown rendering chain | State Management | Medium |
| 4 | `app.ts:157-161` | Greedy regex in list wrapping could produce malformed HTML | Code Quality | Medium |
| 5 | `main.ts:9-18` | Duplicate initialization logic violates DRY principle | Code Quality | Low |

**Total Issues:** 5  
**By Severity:** Critical (0), High (1), Medium (2), Low (2)  
**By Category:** Safety (1), Type Safety (1), State Management (1), Code Quality (2)

---

## Recommendations

### Immediate Actions (High Severity)
- **Issue #2**: Implement `getElementOrThrow` helper and refactor DOM retrieval (5 min fix)
  - Prevents runtime crashes if HTML ids are mismatched
  - Provides clear error messages during development

### Near-term Improvements (Medium Severity)
- **Issue #3**: Refactor `renderMarkdown` with intermediate `const` variables (10 min)
- **Issue #4**: Consider using `marked` library instead of custom regex (or remove list support for MVP) (20 min)
  - Reduces risk of malformed HTML in edge cases
  - More maintainable long-term

### Polish (Low Severity)
- **Issue #1**: Convert interfaces to types (2 min)
- **Issue #5**: Simplify initialization logic (2 min)

**Estimated total refactoring time:** 40 minutes  
**Recommendation:** Apply all fixes before opening the PR for Issue #13.

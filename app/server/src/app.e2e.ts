/**
 * End-to-end tests for the aretil web app.
 * Tests the RFP → pitch workflow.
 */

import { test, expect, Page } from "@playwright/test";

test.describe("aretil web app", () => {
  let page: Page;

  test.beforeEach(async ({ page: testPage }) => {
    page = testPage;
    await page.goto("/");
  });

  test("should load the app with header and input", async () => {
    // Check header
    const header = page.locator("h1");
    await expect(header).toContainText("aretil");

    // Check RFP input section
    const rfpLabel = page.locator("text=RFP");
    await expect(rfpLabel).toBeVisible();

    // Check textarea
    const rfpInput = page.locator("#rfp-input");
    await expect(rfpInput).toBeVisible();
    await expect(rfpInput).toHaveAttribute("placeholder", /Paste an RFP/);

    // Check submit button
    const submitBtn = page.locator("#submit-btn");
    await expect(submitBtn).toBeVisible();
    await expect(submitBtn).toContainText("Generate pitch");
  });

  test("should show error when submitting empty RFP", async () => {
    const submitBtn = page.locator("#submit-btn");
    await submitBtn.click();

    // Check error message appears
    const errorMsg = page.locator(".error");
    await expect(errorMsg).toBeVisible();
    await expect(errorMsg).toContainText("Please paste an RFP");
  });

  test("should generate and display a pitch for an RFP", async () => {
    // Fill RFP input with sample RFP
    const rfpInput = page.locator("#rfp-input");
    const sampleRfp =
      "We are seeking a law firm to advise on a healthcare M&A transaction. " +
      "The target is a mid-sized medical devices company. The deal is expected to close in Q3 2026. " +
      "We need a firm with significant healthcare M&A experience and regulatory expertise.";

    await rfpInput.fill(sampleRfp);

    // Submit
    const submitBtn = page.locator("#submit-btn");
    await submitBtn.click();

    // Verify button is disabled during submission
    await expect(submitBtn).toBeDisabled();

    // Wait for pitch content to appear (with a reasonable timeout)
    const pitchContent = page.locator("#pitch-content");
    await expect(pitchContent).not.toContainText("Your pitch will appear here", {
      timeout: 60000, // 60 seconds for the whole pitch workflow
    });

    // Verify success message
    const successMsg = page.locator(".success");
    await expect(successMsg).toContainText("Pitch generated");

    // Verify copy button is now visible
    const copyBtn = page.locator("#copy-btn");
    await expect(copyBtn).toBeVisible();
    await expect(copyBtn).toContainText("Copy to clipboard");

    // Verify submit button is re-enabled
    await expect(submitBtn).not.toBeDisabled();

    // Verify pitch content contains expected text (should have drafted content)
    const pitchText = await pitchContent.textContent();
    expect(pitchText).toBeTruthy();
    expect(pitchText?.length).toBeGreaterThan(0);
  });

  test("should copy pitch to clipboard", async () => {
    // Generate a pitch first
    const rfpInput = page.locator("#rfp-input");
    const sampleRfp =
      "We need M&A legal services for a healthcare transaction involving regulatory approval.";
    await rfpInput.fill(sampleRfp);

    const submitBtn = page.locator("#submit-btn");
    await submitBtn.click();

    // Wait for pitch to generate
    const successMsg = page.locator(".success");
    await expect(successMsg).toContainText("Pitch generated", { timeout: 60000 });

    // Click copy button
    const copyBtn = page.locator("#copy-btn");
    await copyBtn.click();

    // Verify feedback message changed
    const updatedMsg = page.locator(".success");
    await expect(updatedMsg).toContainText("Copied to clipboard");
  });

  test("should handle API errors gracefully", async () => {
    // This test assumes the API server is not running or returns an error
    const rfpInput = page.locator("#rfp-input");
    await rfpInput.fill("Test RFP content");

    // Intercept and simulate API error
    await page.route("**/api/pitch", (route) => {
      route.abort("failed");
    });

    const submitBtn = page.locator("#submit-btn");
    await submitBtn.click();

    // Wait for error message
    const errorMsg = page.locator(".error");
    await expect(errorMsg).toBeVisible({ timeout: 10000 });
    await expect(errorMsg).toContainText("Error:");
  });
});

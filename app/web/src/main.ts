/**
 * Web app entry point.
 */

import "./styles.css";
import { initializeApp } from "./app.js";

// Initialize the app when the DOM is ready
document.addEventListener("DOMContentLoaded", () => {
  initializeApp();
});

// Fallback in case DOM is already ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeApp);
} else {
  initializeApp();
}

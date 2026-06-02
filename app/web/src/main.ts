/**
 * Web app entry point.
 */

import "./styles.css";
import { initializeApp } from "./app.js";

// Initialize app when DOM is ready or immediately if already loaded
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", initializeApp);
} else {
  initializeApp();
}

/**
 * @vitest-environment jsdom
 */
import { expect, test } from "vitest";
import { initializeFeedbackToggles } from "../feedback/toggle-feedback-entries.js";

test("does not throw when a table cell has no feedback toggle", () => {
    const cell = document.createElement("span");
    cell.className = "table-cell-content";
    document.body.append(cell);

    expect(() => initializeFeedbackToggles()).not.toThrow();
});

import { expect, test } from "vitest";
import { toggleOptionalText } from "../machine-translation-overlay.js";

/**
 * @vitest-environment jsdom
 */

test("show optional text", () => {
    const trigger = document.createElement("button");
    const optionalText = document.createElement("span");
    optionalText.classList.add("hidden");

    toggleOptionalText(trigger, optionalText);
    trigger.click();

    expect(optionalText.classList.contains("block")).toBe(true);
    expect(optionalText.classList.contains("hidden")).toBe(false);

    trigger.click();

    expect(optionalText.classList.contains("block")).toBe(false);
    expect(optionalText.classList.contains("hidden")).toBe(true);

    trigger.click();

    expect(optionalText.classList.contains("block")).toBe(true);
    expect(optionalText.classList.contains("hidden")).toBe(false);
});

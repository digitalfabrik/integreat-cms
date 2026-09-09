// @vitest-environment jsdom
import { expect, test } from "vitest";

/**
 * Dispatch a cancelable beforeunload event and report whether the warning kicked in.
 */
const warningShown = (): boolean => {
    const event = new Event("beforeunload", { cancelable: true });
    window.dispatchEvent(event);
    return event.defaultPrevented;
};

test("a confirmed action is not interrupted by the unsaved-warning", async () => {
    document.body.innerHTML = `
        <form data-unsaved-warning>
            <input id="field" type="text" />
        </form>
        <div id="confirmation-dialog">
            <form id="confirmation-form" method="post"></form>
        </div>
    `;

    // Registers the beforeunload handler and, on load, the form listeners
    await import("../unsaved-warning");
    window.dispatchEvent(new Event("load"));

    expect(warningShown()).toBe(false);

    // The user edits something
    document.getElementById("field").dispatchEvent(new Event("input", { bubbles: true }));
    expect(warningShown()).toBe(true);

    // The user triggers a confirmation button and confirms. The dialog is a separate form, so
    // without clearing the flag the browser would ask a second time -- and staying on the page
    // would silently swallow the action the user just confirmed.
    document.getElementById("confirmation-form").dispatchEvent(new Event("submit", { bubbles: true }));
    expect(warningShown()).toBe(false);
});

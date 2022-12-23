/**
 * Handles toggling boxes on the dashboard
 * @param {Event} event Click event for dashboard containers
 */

import { getCookie } from "./utils/cookies";

const toggleDashboardSection = async ({ target }: Event): Promise<void> => {
    // Toggle arrows of the clicked widget
    const collapsible = (target as HTMLElement).closest(".collapsible") as HTMLElement;
    collapsible.querySelector(".up-arrow").classList.toggle("hidden");
    collapsible.querySelector(".down-arrow").classList.toggle("hidden");
    // Toggle the content div which should be collapsed or expanded
    const content = collapsible.parentNode.querySelector(".collapsible-content") as HTMLElement;
    // Check if content is currently collapsed or not
    if (content.clientHeight === 0) {
        // Temporarily set height to auto to allow to grow to its total potential height
        content.style.height = "auto";
        // Get the actual height
        const potentialHeight = `${content.clientHeight}px`;
        // Immediately reset to zero
        content.style.height = "0px";
        // Set the height to a fixed numerical value with a timeout for the transition
        setTimeout(() => {
            content.style.height = potentialHeight;
        });
        // After the potential height is restored, change this value to "auto" to not break things when window is resized
        const timeoutDuration = 200;
        setTimeout(() => {
            content.style.height = "auto";
        }, timeoutDuration);
        collapsible.removeAttribute("data-collapsed");
    } else {
        // Set height to explicit numerical value instead of "auto" to enable continuous transition
        content.style.height = `${content.clientHeight}px`;
        // Use timeout to allow a smooth transition
        setTimeout(() => {
            content.style.height = "0px";
        });
        collapsible.dataset.collapsed = "";
    }
    // Get the ids of all boxes which are collapsed and have a non-empty id attribute
    const collapsedBoxes = Array.from(document.querySelectorAll("[data-collapsed]:not([id=''])")).map((box) => box.id);
    // Set the scope of the cookie to the first two path segments (slice to 3 because the pathname starts with a leading slash)
    const sliceEnd = 3;
    const cookiePath = window.location.pathname.split("/").slice(0, sliceEnd).join("/");
    // Store the currently collapsed boxes in a cookie
    document.cookie = `collapsed-boxes=${JSON.stringify(collapsedBoxes)};path=${cookiePath}`;
};

window.addEventListener("load", () => {
    document.querySelectorAll(".collapsible").forEach((node) => {
        node.addEventListener("click", toggleDashboardSection);
    });
    // Restore all collapsed boxes
    const collapsedBoxes = getCookie("collapsed-boxes");
    if (collapsedBoxes) {
        JSON.parse(collapsedBoxes).forEach((id: string) => {
            const collapsible = document.querySelector(`.collapsible[id='${id}']`) as HTMLElement;
            if (collapsible) {
                collapsible.querySelector(".up-arrow").classList.add("hidden");
                collapsible.querySelector(".down-arrow").classList.remove("hidden");
                collapsible.parentNode.querySelector(".collapsible-content").classList.add("h-0");
                collapsible.dataset.collapsed = "";
            }
        });
    }
});

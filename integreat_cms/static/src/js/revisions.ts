/**
 * This file contains all functions which are needed for the diff calculation of revisions.
 */

import HtmlDiff from "htmldiff-js";

const calculateTooltipPositions = (target: Element, tooltip: Element, lastItem: Element) => {
    const targetRect = target.getBoundingClientRect();
    const lastItemRect = lastItem.getBoundingClientRect();
    const tooltipRect = tooltip.getBoundingClientRect();

    const scrollTop = window.scrollY || document.documentElement.scrollTop;

    const tooltipWidth = tooltipRect.width;

    const timelineItemPadding = 6;
    const additionalItemOffset = 24;

    const exceedsBoundary = targetRect.left + tooltipWidth > lastItemRect.right;

    const lastItemOffset = exceedsBoundary ? tooltipWidth - additionalItemOffset : 0;

    const tooltipX = targetRect.left - lastItemOffset;
    const tooltipY = targetRect.bottom + scrollTop + timelineItemPadding;

    return [`${tooltipY}px`, `${tooltipX}px`];
};

const toggleActionButtonVisibility = (revision: number, revisionCount: number, revisionElement: HTMLElement) => {
    document.querySelectorAll(".action-buttons button").forEach((button) => {
        const buttonHtml = button as HTMLElement;
        const equivalentStatus = buttonHtml.dataset.status === revisionElement.dataset.status;
        const dataMaxPresentIfLatestRevision = (revision === revisionCount) !== (buttonHtml.dataset.max === undefined);

        if (equivalentStatus && dataMaxPresentIfLatestRevision) {
            button.classList.remove("hidden");
        } else {
            button.classList.add("hidden");
        }
    });
};

window.addEventListener("load", () => {
    // Iterate over revisions and calculate diff
    document.querySelectorAll(".revision-plain").forEach((revision) => {
        // The div wrapper around plain content and diff
        const parent = revision.parentNode;
        // The numeric id of the revision
        const idStartsAt = 9;
        const id = parseInt((parent as HTMLElement).id.substring(idStartsAt), 10);
        // The plain content div of the previous revision
        const prevRevision = document.getElementById(`revision-${id - 1}`)?.querySelector(":scope > .revision-plain");
        // Calculate the actual diff and insert into the diff div
        if (parent.querySelector(":scope > .revision-diff")) {
            parent.querySelector(":scope > .revision-diff").innerHTML = HtmlDiff.execute(
                prevRevision?.innerHTML || "",
                revision.innerHTML
            );
        }
    });

    const timelineItems = document.querySelectorAll(".timeline-item");

    const revisionCount = Array.from(timelineItems).length;
    const lastTimelineItem = Array.from(timelineItems)[revisionCount - 1];

    const tooltip = document.getElementById("tooltip");
    const versionLine = document.getElementById("version-text");
    const authorLine = document.getElementById("author-text");
    const dateLine = document.getElementById("date-text");
    const hixLine = document.getElementById("hix-text");

    timelineItems.forEach((item) => {
        item.addEventListener("click", () => {
            const revision = Number(item.getAttribute("data-number"));

            document.querySelectorAll(".timeline-item").forEach((it) => {
                it.classList.remove("active");
            });

            item.classList.add("active");

            document.querySelectorAll(".revision-wrapper").forEach((node) => {
                node.classList.add("hidden");
            });

            document.getElementById(`revision-${revision}`).classList.remove("hidden");

            const revisionElement = document.getElementById(`revision-${revision}`);

            versionLine.textContent = revision.toString();
            authorLine.textContent = revisionElement.dataset.editor;
            dateLine.textContent = revisionElement.dataset.date;

            if (hixLine) {
                hixLine.textContent = revisionElement.dataset.hix || "-";
            }

            tooltip.classList.remove("hidden");

            const [top, left] = calculateTooltipPositions(item, tooltip, lastTimelineItem);

            tooltip.style.top = top;
            tooltip.style.left = left;

            toggleActionButtonVisibility(revision, revisionCount, revisionElement);
        });
    });

    // Simulate initial input after page load
    lastTimelineItem.dispatchEvent(new Event("click"));
});

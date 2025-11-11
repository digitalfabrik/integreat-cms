/**
 * This file contains all functions which are needed for the diff calculation of revisions.
 */

import HtmlDiff from "htmldiff-js";

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
    const versionHistory = document.getElementById("version-history");

    const prevButton = document.getElementById("button-prev");
    const nextButton = document.getElementById("button-next");

    const revisionCount = Array.from(timelineItems).length;
    const lastTimelineItem = Array.from(timelineItems)[revisionCount - 1];

    const tooltip = document.getElementById("tooltip");
    const versionLine = document.getElementById("version-text");
    const authorLine = document.getElementById("author-text");
    const dateLine = document.getElementById("date-text");
    const hixLine = document.getElementById("hix-text");

    const calculateTooltipPositions = (target: Element, tooltip: Element) => {
        const targetRect = target.getBoundingClientRect();
        const tooltipRect = tooltip.getBoundingClientRect();

        const viewportWidth = window.innerWidth;
        const tooltipWidth = tooltipRect.width;
        const scrollTop = window.scrollY || document.documentElement.scrollTop;

        const verticalOffset = 10;
        const horizontalOffset = 10;

        const rightIcon = document.getElementById("button-next") as HTMLElement;
        const rightIconWidth = rightIcon ? rightIcon.getBoundingClientRect().width : 0;

        const availableWidth = viewportWidth - rightIconWidth;

        let tooltipX = targetRect.left;
        const tooltipY = targetRect.bottom + scrollTop + verticalOffset;

        if (tooltipX + tooltipWidth > availableWidth) {
            tooltipX = targetRect.right - tooltipWidth - horizontalOffset;
        }

        if (tooltipX < horizontalOffset) {
            tooltipX = horizontalOffset;
        }

        return [`${tooltipY}px`, `${tooltipX}px`];
    };

    const toggleActionButtonVisibility = (revision: number, revisionCount: number) => {
        const revisionElement = document.getElementById(`revision-${revision}`);

        document.querySelectorAll(".action-buttons button").forEach((button) => {
            const buttonHtml = button as HTMLElement;
            const equivalentStatus = buttonHtml.dataset.status === revisionElement.dataset.status;
            const dataMaxPresentIfLatestRevision =
                (revision === revisionCount) !== (buttonHtml.dataset.max === undefined);

            if (equivalentStatus && dataMaxPresentIfLatestRevision) {
                button.classList.remove("hidden");
            } else {
                button.classList.add("hidden");
            }
        });
    };

    const repositionTooltip = () => {
        const tooltip = document.getElementById("tooltip");
        const currentTimelineItem = document.querySelector(".timeline-item.active");

        const [top, left] = calculateTooltipPositions(currentTimelineItem, tooltip);

        tooltip.style.top = top;
        tooltip.style.left = left;
    };

    const toggleVersionHistoryControls = () => {
        const timelineItems = document.querySelectorAll(".timeline-item");

        const firstItem = timelineItems[0];
        const lastItem = timelineItems[timelineItems.length - 1];

        const firstItemActive = firstItem.classList.contains("active");
        const lastItemActive = lastItem.classList.contains("active");

        if (firstItemActive) {
            prevButton.classList.add("disabled");
            prevButton.classList.remove("enabled");
        } else {
            prevButton.classList.remove("disabled");
            prevButton.classList.add("enabled");
        }

        if (lastItemActive) {
            nextButton.classList.add("disabled");
            nextButton.classList.remove("enabled");
        } else {
            nextButton.classList.remove("disabled");
            nextButton.classList.add("enabled");
        }
    };

    const updateActiveTimelineItem = (item: Element) => {
        const revision = Number(item.getAttribute("data-number"));

        document.getElementsByName("revision")[0].setAttribute("value", revision.toString());

        document.querySelectorAll(".timeline-item").forEach((it) => {
            it.classList.remove("active");
        });

        item.classList.add("active");

        document.querySelectorAll(".revision-wrapper").forEach((node) => {
            node.classList.add("hidden");
        });

        const revisionElement = document.getElementById(`revision-${revision}`);
        revisionElement.classList.remove("hidden");

        versionLine.textContent = revision.toString();
        authorLine.textContent = revisionElement.dataset.editor;
        dateLine.textContent = revisionElement.dataset.date;

        if (hixLine) {
            hixLine.textContent = revisionElement.dataset.hix || "-";
        }

        tooltip.classList.remove("hidden");

        const [top, left] = calculateTooltipPositions(item, tooltip);

        tooltip.style.top = top;
        tooltip.style.left = left;

        toggleActionButtonVisibility(revision, revisionCount);

        toggleVersionHistoryControls();
    };

    timelineItems.forEach((item) => {
        item.addEventListener("click", () => {
            const revision = Number(item.getAttribute("data-number"));

            updateActiveTimelineItem(item);

            toggleActionButtonVisibility(revision, revisionCount);

            toggleVersionHistoryControls();
        });
    });

    const scrollToElement = (element: Element, container: HTMLElement) => {
        const containerRect = container.getBoundingClientRect();
        const elementRect = element.getBoundingClientRect();

        const containerScrollLeft = container.scrollLeft;
        const containerWidth = container.clientWidth;
        const elementWidth = element.clientWidth;

        const scrollLeft = elementRect.left - containerRect.left + containerScrollLeft;
        const scrollRight = scrollLeft + elementWidth;
        const containerRight = containerScrollLeft + containerWidth;

        if (scrollLeft < containerScrollLeft) {
            // eslint-disable-next-line no-param-reassign
            container.scrollLeft += scrollLeft - containerScrollLeft;
        } else if (scrollRight > containerRight) {
            // eslint-disable-next-line no-param-reassign
            container.scrollLeft += scrollRight - containerRight;
        }
    };

    const selectNextTimelineItem = () => {
        const activeItem = document.querySelector(".timeline-item.active");
        if (!activeItem) {
            return;
        }

        const nextItem = activeItem.nextElementSibling;
        if (nextItem && nextItem.classList.contains("timeline-item")) {
            updateActiveTimelineItem(nextItem);

            scrollToElement(nextItem, versionHistory);
        }
    };

    const selectPrevTimelineItem = () => {
        const activeItem = document.querySelector(".timeline-item.active");
        if (!activeItem) {
            return;
        }

        const prevItem = activeItem.previousElementSibling;
        if (prevItem && prevItem.classList.contains("timeline-item")) {
            updateActiveTimelineItem(prevItem);
            scrollToElement(prevItem, versionHistory);
        }
    };

    // Check if an element is within the visible range of its container
    const isElementInView = (element: HTMLElement, container: HTMLElement) => {
        const containerRect = container.getBoundingClientRect();
        const elementRect = element.getBoundingClientRect();
        return elementRect.left >= containerRect.left && elementRect.right <= containerRect.right;
    };

    let previousScrollLeft = 0;

    const autoSelectTimelineItem = () => {
        const versionHistory = document.getElementById("version-history");
        if (!versionHistory) {
            console.warn("Element with id 'version-history' not found.");
            return;
        }

        const activeItem: HTMLElement | null = versionHistory.querySelector(".timeline-item.active");
        if (!activeItem) {
            console.warn("Active timeline item not found.");
            return;
        }

        const allItems: HTMLElement[] = Array.from(versionHistory.querySelectorAll(".timeline-item"));
        const currentIndex = allItems.indexOf(activeItem);

        if (currentIndex === -1) {
            console.warn("Active item is not in the list of timeline items.");
            return;
        }

        let targetItem: HTMLElement | undefined;

        if (versionHistory.scrollLeft > previousScrollLeft) {
            // Scrolling right
            if (currentIndex < allItems.length - 1) {
                targetItem = allItems[currentIndex + 1];
            }
        } else if (versionHistory.scrollLeft < previousScrollLeft) {
            // Scrolling left
            if (currentIndex > 0) {
                targetItem = allItems[currentIndex - 1];
            }
        }

        if (targetItem) {
            if (isElementInView(targetItem, versionHistory)) {
                // If the target item is in view, select it
                targetItem.click();
            } else {
                // Prevent further scrolling until the target item is visible
                // Monitor for when the target item comes into view
                const observer = new MutationObserver(() => {
                    if (isElementInView(targetItem, versionHistory)) {
                        targetItem.click();
                        observer.disconnect();
                    }
                });

                observer.observe(versionHistory, { childList: true, subtree: true });
            }
        }

        // Update the previous scroll position
        previousScrollLeft = versionHistory.scrollLeft;

        repositionTooltip();
    };

    document.querySelectorAll(".timeline-item").forEach((item) => {
        item.addEventListener("click", () => {
            updateActiveTimelineItem(item);
        });
    });

    if (nextButton) {
        nextButton.addEventListener("click", () => {
            selectNextTimelineItem();
        });
    }

    if (prevButton) {
        prevButton.addEventListener("click", () => {
            selectPrevTimelineItem();
        });
    }

    document.addEventListener("keydown", (event) => {
        if (event.key === "ArrowRight") {
            selectNextTimelineItem();
        } else if (event.key === "ArrowLeft") {
            selectPrevTimelineItem();
        }
    });

    if (versionHistory) {
        versionHistory.scrollLeft = versionHistory.scrollWidth;
        versionHistory.addEventListener("scroll", autoSelectTimelineItem);
    }

    // Move initial position to the very end of the timeline
    if (lastTimelineItem) {
        lastTimelineItem.dispatchEvent(new Event("click"));
    }
});

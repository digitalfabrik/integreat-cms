/**
 * Polls the progress of machine translation batches shown as a spinner icon
 * in a content list view (e.g. the page tree).
 *
 * Attached to a stable ancestor of the list (root element) via
 * `data-js-mt-progress-poll`, not to individual rows - rows can be inserted
 * dynamically later (e.g. async page tree loading, see `fetch-subpages.ts`),
 * and no longer trigger the usual per-element bootstrap once inserted.
 * Instead, this re-scans `root` for new `[data-mt-task-id]` elements once the
 * `subpages-loaded` event fires (mirrors the pattern in `bulk-actions.ts`).
 *
 * Every object/language pair that a single triggered translation covers
 * shares one Celery task id, so rather than polling per row, all elements
 * sharing a `data-mt-task-id` are grouped and only one poll runs per task.
 *
 * Once a task's poll resolves, a one-off aggregate banner is also shown
 * (not the per-page report) via the shared `utils/mt-report-banner` module -
 * also used by `content-edit-lock.ts` for the same banners, discovered
 * through the heartbeat instead of a dedicated poll there.
 *
 * @module mt-progress-poll
 */
import { defineFeature } from "../utils/define-feature";
import { FAILURE_BANNER_CLASS, showBanner, showReportBanners } from "../utils/mt-report-banner";

const POLL_INTERVAL_MS = 5_000;
const RUNNING_STATES = new Set(["PENDING", "STARTED", "IN_PROGRESS", "RETRY"]);

type PageLanguagePatch = {
    translation_state: string;
    title?: string;
    slug?: string;
    status?: string;
    last_updated?: string;
};

type PagesData = Record<string, Record<string, PageLanguagePatch>>;

/**
 * Re-enables the row and, if a patch for this page/language is available,
 * updates its status text, title/slug, and last-updated date in place.
 *
 * @param element The status-cell element that was showing the spinner
 * @param patch The fresh data for this page/language, if any (absent e.g.
 * if the task failed outright rather than reporting per-object results)
 */
const patchRow = (element: HTMLElement, patch: PageLanguagePatch | undefined) => {
    const row = element.closest<HTMLElement>("tr");
    row?.classList.remove("opacity-50", "pointer-events-none");

    element.classList.add("hidden");
    const statusText = element.parentElement?.querySelector<HTMLElement>("[data-mt-status-text]");
    statusText?.classList.remove("hidden");
    if (!patch) {
        return;
    }
    if (statusText && patch.status) {
        statusText.textContent = patch.status;
    }
    const titleEl = row?.querySelector<HTMLElement>(".title-slug");
    if (titleEl && patch.title) {
        titleEl.textContent = patch.title;
        titleEl.setAttribute("data-title-slug", patch.slug ?? "");
    }
    const lastUpdatedEl = row?.querySelector<HTMLElement>("[data-mt-last-updated]");
    if (lastUpdatedEl && patch.last_updated) {
        // Matches Django's `|date:"SHORT_DATE_FORMAT"` rendering (e.g.
        // "06.08.2026" for German) closely enough by using the same locale
        // the page itself was rendered in.
        lastUpdatedEl.textContent = new Intl.DateTimeFormat(document.documentElement.lang, {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
        }).format(new Date(patch.last_updated));
    }
};

/**
 * Called once a task's poll resolves. For each tracked element, shows
 * whichever "finished" appearance applies, based on which marker attribute
 * the element carries: either revealing the matching outcome icon next to
 * a lang-grid spinner, or patching the status-cell row via `patchRow`.
 *
 * @param elements All elements (spinners and/or status cells) tracked for
 * the task that just finished
 * @param pagesData Per-object, per-language patch data from the task
 * result, if any (absent e.g. if the task failed outright)
 */
const showFinished = (elements: HTMLElement[], pagesData: PagesData | undefined) => {
    elements.forEach((element) => {
        const { mtPageId: pageId, mtLanguageSlug: languageSlug } = element.dataset;
        const patch = pagesData?.[pageId]?.[languageSlug];

        if (element.hasAttribute("data-mt-spinner")) {
            // `element` is the spinner itself; reveal whichever sibling
            // matches the outcome this object/language actually resolved
            // to, falling back to the generic "finished" icon if there's no
            // patch for it (e.g. the task failed outright) or no matching
            // outcome icon for its `translation_state`.
            element.classList.add("hidden");
            const outcomeIcon =
                patch && element.parentElement?.querySelector(`[data-mt-outcome-icon="${patch.translation_state}"]`);
            const fallbackIcon = element.parentElement?.querySelector("[data-mt-finished]");
            (outcomeIcon || fallbackIcon)?.classList.remove("hidden");
            return;
        }
        if (element.hasAttribute("data-mt-status-cell")) {
            patchRow(element, patch);
        }
    });
};

/**
 * Polls a single Celery task until it leaves a running state, then patches
 * every tracked element for it and shows the resulting outcome/failure
 * banner. Reschedules itself via `setTimeout` (not `setInterval`), so the
 * next poll only fires once the previous one has actually resolved.
 *
 * @param root The feature's root element (for banner placement)
 * @param taskId The Celery task id being polled
 * @param url The task-progress endpoint to poll
 * @param elements The elements to patch once this task finishes - the same
 * shared, mutable array `pollNewTasks` may still be appending to while this
 * is pending, see the comment further down
 * @param knownElementsByTask The tracking map this task id should be
 * removed from once its poll resolves
 */
const pollTask = async (
    root: HTMLElement,
    taskId: string,
    url: string,
    elements: HTMLElement[],
    knownElementsByTask: Map<string, HTMLElement[]>
) => {
    const response = await fetch(url);
    const data = await response.json();
    if (RUNNING_STATES.has(data.status)) {
        setTimeout(() => pollTask(root, taskId, url, elements, knownElementsByTask), POLL_INTERVAL_MS);
        return;
    }
    // `elements` is the same array `knownElementsByTask` holds for this task -
    // any rows discovered later (e.g. subpages that only loaded after this
    // poll started, see below) were pushed into it in the meantime, so this
    // patches everything found so far, not just what was known at the start.
    showFinished(elements, data.details?.pages);
    knownElementsByTask.delete(taskId);

    const bannerContainer = root.querySelector("[data-mt-report-banner]");
    if (data.status === "FAILURE") {
        showBanner(bannerContainer, FAILURE_BANNER_CLASS, data.details?.message);
    } else {
        showReportBanners(bannerContainer, root.dataset.mtReportUrl);
    }
};

/**
 * Scans `root` for `[data-mt-task-id]` elements and starts polling any task
 * id not already being tracked. Safe to call repeatedly (e.g. once on
 * initial load, then again on every `subpages-loaded` event) - elements
 * for an already-tracked task id are just added to its existing group
 * instead of starting a second, redundant poll loop for the same task.
 *
 * @param root The feature's root element to scan
 * @param knownElementsByTask The shared tracking map, mutated in place
 */
const pollNewTasks = (root: HTMLElement, knownElementsByTask: Map<string, HTMLElement[]>) => {
    const elements = Array.from(root.querySelectorAll<HTMLElement>("[data-mt-task-id]"));

    elements.forEach((element) => {
        const { mtTaskId, mtTaskProgressUrl } = element.dataset;

        const existingGroup = knownElementsByTask.get(mtTaskId);
        if (existingGroup) {
            if (!existingGroup.includes(element)) {
                existingGroup.push(element);
            }
            return;
        }

        // First time this task id has been seen: start tracking and polling
        // it, with a mutable array that later scans (e.g. once collapsed
        // subpages sharing this task finish loading) can still add to.
        const groupElements = [element];
        knownElementsByTask.set(mtTaskId, groupElements);
        setTimeout(
            () => pollTask(root, mtTaskId, mtTaskProgressUrl, groupElements, knownElementsByTask),
            POLL_INTERVAL_MS
        );
    });
};

export default defineFeature((root) => {
    const knownElementsByTask = new Map<string, HTMLElement[]>();
    pollNewTasks(root, knownElementsByTask);
    document.addEventListener("subpages-loaded", () => pollNewTasks(root, knownElementsByTask));
});

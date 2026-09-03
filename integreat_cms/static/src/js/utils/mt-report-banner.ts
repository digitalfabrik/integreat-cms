/**
 * Shared helpers for showing machine translation outcome/failure banners.
 * Used by `feature/mt-progress-poll.ts` (list view) and `content-edit-lock.ts`
 * (source-page editor) - both need to render the exact same banners, just
 * discovered through different polling mechanisms.
 *
 * @module mt-report-banner
 */

// Same shared banner classes the server-rendered banners in `messages.html`
// use (see `.banner-*` in `style.scss`). Only the color coding lives here -
// the actual text is sent by the backend (translated there, so it reflects
// the requesting user's language).
const OUTCOME_BANNER_CLASSNAMES: Record<string, string> = {
    FULL_SUCCESS: "banner-success",
    PARTIAL_SUCCESS: "banner-warning",
};
export const FAILURE_BANNER_CLASS = "banner-error";

/**
 * Builds and inserts one banner into `container`. Not shown via Django's
 * messages framework since that only renders on a fresh page load - callers
 * of this module deliberately avoid reloading.
 *
 * @param container The banner placeholder to append into - callers look
 * this up however fits their own DOM structure, so it's passed in directly
 * rather than assumed to live at a fixed spot relative to some root
 */
export const showBanner = (container: Element | null, className: string, text: string) => {
    if (!container) {
        return;
    }
    const banner = document.createElement("div");
    banner.className = className;
    banner.setAttribute("role", "alert");
    const paragraph = document.createElement("p");
    paragraph.textContent = text;
    banner.append(paragraph);
    container.append(banner);
};

/**
 * Fetches (and, server-side, consumes) any queued reports and shows one
 * aggregate banner per report - not the per-page breakdown. Safe to call
 * redundantly: the report endpoint is a destructive read, so a report
 * already consumed by another trigger just comes back empty here.
 *
 * @param container The banner placeholder to append into
 * @param reportUrl The report endpoint to fetch, if known
 */
export const showReportBanners = async (container: Element | null, reportUrl: string | undefined) => {
    if (!container || !reportUrl) {
        return;
    }
    const response = await fetch(reportUrl);
    const data = await response.json();
    data.reports?.forEach((report: { outcome: string; message: string }) => {
        const className = OUTCOME_BANNER_CLASSNAMES[report.outcome];
        if (className) {
            showBanner(container, className, report.message);
        }
    });
};

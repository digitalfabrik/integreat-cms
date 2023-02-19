/*
 * Enable Preact debugging during development
 *
 * Install the Preact Devtools browser extension to make use of it:
 *
 *     https://preactjs.github.io/preact-devtools/
 */
/* eslint-disable import/first */
if (process.env.NODE_ENV !== "production") {
    /* eslint-disable-next-line global-require */
    require("preact/debug");
}
/* Babel requirements & polyfills */
import "core-js/stable";
import "regenerator-runtime/runtime";
import "whatwg-fetch"; // IE11: Element.closest

import "./css/style.scss";

import "./js/auto-file-download.ts";
import "./js/tree-drag-and-drop.ts";
import "./js/rss-feed.ts";
import "./js/collapsible-boxes.ts";
import "./js/push-notifications.ts";
import "./js/filter-form.ts";
import "./js/copy-clipboard.ts";
import "./js/bulk-actions.ts";
import "./js/confirmation-popups.ts";
import "./js/revisions.ts";
import "./js/search-query.ts";

import "./js/forms/slug-error.ts";
import "./js/forms/update-permalink.ts";
import "./js/forms/distribute-sidebar-boxes.ts";

import "./js/languages/country-flag-fields.ts";

import "./js/regions/conditional-fields.ts";

import "./js/feedback/toggle-feedback-entries.ts";

import "./js/grids/toggle-grid-checkbox.ts";

import "./js/chat/send-chat-message.ts";
import "./js/chat/delete-chat-message.ts";

import "./js/events/event-query-pois.ts";
import "./js/events/conditional-fields.ts";
import "./js/events/auto-complete.ts";

import "./js/pages/fetch-subpages.ts";
import "./js/pages/toggle-subpages.ts";
import "./js/pages/page-api-token.ts";
import "./js/pages/page-mirroring.ts";
import "./js/pages/page-order.ts";
import "./js/pages/page-permissions.ts";
import "./js/pages/page-side-by-side.ts";
import "./js/pages/unset-translation-state.ts";
import "./js/pages/xliff-file-upload.ts";
import "./js/pages/xliff-import.ts";
import "./js/pages/xliff-export-overlay.ts";
import "./js/pages/page-preview.ts";

import "./js/mfa/add-key.ts";
import "./js/mfa/login.ts";

import "./js/analytics/statistics-charts.ts";
import "./js/analytics/translation_coverage.ts";
import "./js/analytics/linkcheck-widget.ts";

import "./js/translations/budget-graph.ts";
import "./js/translations/translate-pages-forms.ts";

import "./js/user/user-creation-workflow.ts";
import "./js/user/user-roles.ts";
import "./js/user/organization.ts";

import { createIconsAt } from "./js/utils/create-icons";

import "./js/charCounter.ts";

import "./js/media-management/index.tsx";
import "./js/media-management/select-media.tsx";
import "./js/forms/icon-field.tsx";

import "./js/pagination/pagination.ts";

import "./js/tutorial-overlay.ts";

import "./js/unsaved-warning";

import "./js/pois/poi-actions.ts";
import "./js/pois/opening-hours/index.tsx";

import "./js/menu.ts";

import "./js/poi-categories/poicategory-colors-icons.ts";

// IE11: fetch
/* eslint-disable-next-line @typescript-eslint/no-var-requires */
require("element-closest").default(window);

window.addEventListener("DOMContentLoaded", () => {
    createIconsAt(document.documentElement);
    const event = new Event("icon-load");
    window.dispatchEvent(event);
});

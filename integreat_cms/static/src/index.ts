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

import "./js/auto-file-download";
import "./js/tree-drag-and-drop";
import "./js/rss-feed";
import "./js/collapsible-boxes";
import "./js/push-notifications";
import "./js/filter-form";
import "./js/copy-clipboard";
import "./js/bulk-actions";
import "./js/conditional-fields";
import "./js/confirmation-popups";
import "./js/machine-translation-overlay";
import "./js/revisions";
import "./js/search-query";

import "./js/forms/slug-error";
import "./js/forms/update-permalink";
import "./js/forms/distribute-sidebar-boxes";

import "./js/languages/country-flag-fields";

import "./js/regions/conditional-fields";
import "./js/regions/fake-disabled-checkboxes";

import "./js/feedback/toggle-feedback-entries";

import "./js/grids/toggle-grid-checkbox";

import "./js/chat/send-chat-message";
import "./js/chat/delete-chat-message";

import "./js/events/event-query-pois";
import "./js/events/conditional-fields";
import "./js/events/auto-complete";

import "./js/pages/fetch-subpages";
import "./js/pages/toggle-subpages";
import "./js/pages/page-api-token";
import "./js/pages/page-mirroring";
import "./js/pages/page-order";
import "./js/pages/page-permissions";
import "./js/pages/page-side-by-side";
import "./js/pages/unset-translation-state";
import "./js/pages/xliff-file-upload";
import "./js/pages/xliff-import";
import "./js/pages/xliff-export-overlay";
import "./js/pages/page-preview";

import "./js/mfa/add-key";
import "./js/mfa/login";

import "./js/offers/zammad";

import "./js/analytics/statistics-charts";
import "./js/analytics/translation_coverage";
import "./js/analytics/linkcheck-widget";
import "./js/analytics/hix-list";

import "./js/translations/budget-graph";

import "./js/user/user-creation-workflow";
import "./js/user/user-roles";
import "./js/user/organization";

import { createIconsAt } from "./js/utils/create-icons";

import "./js/charCounter";

import "./js/media-management/index";
import "./js/media-management/select-media";
import "./js/forms/icon-field";

import "./js/pagination/pagination";

import "./js/tutorial-overlay";

import "./js/unsaved-warning";

import "./js/pois/poi-actions";
import "./js/pois/opening-hours/index";

import "./js/menu";

import "./js/poi-categories/poicategory-colors-icons";

// IE11: fetch
/* eslint-disable-next-line @typescript-eslint/no-var-requires */
require("element-closest").default(window);

window.addEventListener("DOMContentLoaded", () => {
    createIconsAt(document.documentElement);
    const event = new Event("icon-load");
    window.dispatchEvent(event);
});

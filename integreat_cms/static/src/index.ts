/// <reference types="webpack-env" />
/**
 * Main entry point for the CMS frontend bundle.
 *
 * Imports all legacy modules (directly executed on load) and bootstraps all
 * feature modules — self-contained components scoped to a root DOM element.
 * Feature modules live in `js/feature/` and are discovered automatically via
 * `require.context`. Any element with a `data-js-<module-name>` attribute is
 * used as the root for the corresponding module.
 *
 * To enable Preact debugging, install the Preact Devtools browser extension:
 *
 *     https://preactjs.github.io/preact-devtools/
 *
 * @module index
 */
/* eslint-disable import/first */
if (process.env.NODE_ENV !== "production") {
    /* eslint-disable-next-line @typescript-eslint/no-require-imports, global-require */
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
import "./js/language-tabs";
import "./js/machine-translation-overlay";
import "./js/revisions";
import "./js/event-duration";

import "./js/forms/slug-error";
import "./js/forms/update-permalink";
import "./js/forms/distribute-sidebar-boxes";

import "./js/languages/country-flag-fields";
import "./js/languages/language-color-fields";
import "./js/languages/language-tree-node-form";

import "./js/regions/conditional-fields";
import "./js/regions/fake-disabled-checkboxes";

import "./js/feedback/toggle-feedback-entries";

import "./js/grids/toggle-grid-checkbox";

import "./js/chat/send-chat-message";
import "./js/chat/delete-chat-message";

import "./js/poi-box";
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
import "./js/analytics/statistics-page-accesses";

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
import "./js/dashboard/broken-links";
import "./js/dashboard/translation-coverage";

// IE11: fetch
/* eslint-disable-next-line @typescript-eslint/no-require-imports */
require("element-closest").default(window);

const initedModules = new WeakMap<HTMLElement, Set<string>>();

const markInited = (el: HTMLElement, key: string) => {
    if (!initedModules.has(el)) {
        initedModules.set(el, new Set());
    }
    initedModules.get(el)!.add(key);
};

const hasInited = (el: HTMLElement, key: string) => initedModules.get(el)?.has(key) ?? false;

const featureContext = require.context("./js/feature", true, /\.ts$/);

const keyToModuleName = (key: string): string => {
    const withoutExt = key.replace(/\.ts$/, "").replace(/\/index$/, "");
    return withoutExt.replace(/^\.\//, "").replace(/\//g, "-");
};

const bootstrapModules = async (root: ParentNode = document) => {
    const initPromises: Promise<void>[] = [];
    for (const key of featureContext.keys()) {
        const moduleName = keyToModuleName(key);
        const elements = Array.from(root.querySelectorAll<HTMLElement>(`[data-js-${moduleName}]`)).filter(
            (el) => !hasInited(el, moduleName)
        );
        for (const element of elements) {
            initPromises.push(
                (async () => {
                    try {
                        const mod = await featureContext(key);
                        if (typeof mod.default !== "function") {
                            throw new Error(`${key} does not have a default export function`);
                        }
                        if (mod.default.length < 1) {
                            throw new Error(`${key} default export does not accept a root element`);
                        }
                        await (mod.default as FeatureModuleInit)(element);
                        markInited(element, moduleName);
                    } catch (error) {
                        console.error(`[bootstrapModules] Failed to init ${moduleName}`, error, element);
                    }
                })()
            );
        }
    }
    await Promise.all(initPromises);
};

window.addEventListener("DOMContentLoaded", () => {
    bootstrapModules();
    createIconsAt(document.documentElement);
    const event = new Event("icon-load");
    window.dispatchEvent(event);
});

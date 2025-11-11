/*
 * Enable Preact debugging during development
 *
 * Install the Preact Devtools browser extension to make use of it:
 *
 *     https://preactjs.github.io/preact-devtools/
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
import "./js/collapsible-boxes";
import "./js/filter-form";
import "./js/copy-clipboard";
import "./js/bulk-actions";
import "./js/conditional-fields";
import "./js/confirmation-popups";
import "./js/language-tabs";
import "./js/machine-translation-overlay";
import "./js/menu";

import "./js/forms/slug-error";
import "./js/forms/update-permalink";
import "./js/forms/distribute-sidebar-boxes";

import "./js/regions/fake-disabled-checkboxes";

import "./js/feedback/toggle-feedback-entries";

import "./js/grids/toggle-grid-checkbox";

import "./js/chat/send-chat-message";
import "./js/chat/delete-chat-message";

import "./js/poi-box";

import "./js/pages/fetch-subpages";
import "./js/pages/toggle-subpages";
import "./js/pages/page-preview";

import "./js/mfa/login";

import "./js/offers/zammad";

import "./js/analytics/statistics-charts";
import "./js/analytics/statistics-page-accesses";
import "./js/analytics/translation_coverage";
import "./js/analytics/hix-list";

import "./js/translations/budget-graph";

import "./js/user/user-creation-workflow";
import "./js/user/user-roles";
import "./js/user/organization";

import { createIconsAt } from "./js/utils/create-icons";

import "./js/media-management/index";
import "./js/media-management/select-media";
import "./js/forms/icon-field";

import "./js/pagination/pagination";

import "./js/unsaved-warning";

import "./js/pois/poi-actions";
import "./js/pois/opening-hours/index";

import { registry } from "./registry";
// IE11: fetch
/* eslint-disable-next-line @typescript-eslint/no-require-imports */
require("element-closest").default(window);

const markInited = (el: HTMLElement, key: string) => {
    const anyEl = el as any;
    anyEl.inited ??= new Set<string>();
    anyEl.inited.add(key);
};

const hasInited = (el: HTMLElement, key: string) => (el as any).inited?.has(key);

/**
 *
 * @function bootstrap
 *
 * A function that initializes all registered modules from registry.ts to the element(s) they are attached to in the DOM
 * with the attribute "data-js-<moduleName>".
 * -
 * - it imports the module for the element
 *
 * @param root
 */
export const bootstrapModules = async (root: ParentNode = document) => {
    const registeredModules = Object.keys(registry);
    const dataAttributes = registeredModules.map((k) => `[data-js-${k}]`).join(", ");
    const rootElements = root.querySelectorAll<HTMLElement>(dataAttributes);

    const initPromises = [];
    for (const element of rootElements) {
        const nextPromises = registeredModules
            .filter((moduleName) => element.hasAttribute(`data-js-${moduleName}`) && !hasInited(element, moduleName))
            .map(async (moduleName) => {
                try {
                    const mod = await registry[moduleName]();
                    await mod.default(element);
                    markInited(element, moduleName);
                } catch (error) {
                    console.error(`[bootstrapModules] Failed to init ${moduleName}`, error, element);
                }
            });
        initPromises.push(...nextPromises);
    }
    await Promise.all(initPromises);
};

window.addEventListener("DOMContentLoaded", () => {
    createIconsAt(document.documentElement);
    const event = new Event("icon-load");
    window.dispatchEvent(event);
    bootstrapModules();
});

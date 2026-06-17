/**
 * Automatically triggers a file download by programmatically clicking the root element.
 *
 * Attached to an `<a>` element via `data-js-auto-file-download`.
 * The root must be an `<a>` element with a `href` attribute pointing to the file to download.
 * The click is delayed by 500 ms to allow the page to finish rendering before the download starts.
 *
 * @module auto-file-download
 */

import { defineFeature } from "../utils/define-feature";

export default defineFeature((root) => {
    const timeoutDuration = 500;
    setTimeout(() => {
        (root as HTMLLinkElement).click();
    }, timeoutDuration);
});

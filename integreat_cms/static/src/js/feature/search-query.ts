/**
 * Provides live search suggestions for list view tables.
 *
 * Attached to the root element via `data-js-search-query`.
 * Expects the following elements within root:
 *   - `#table-search-input`      — the text input, with `data-url`, `data-object-type`, and `data-archived` attributes
 *   - `#table-search-suggestions` — the dropdown list for suggestions
 *   - `#search-submit-btn`        — the submit button
 *   - `#search-reset-btn`         — the reset button (optional)
 *
 * On each keystroke (debounced 300 ms) a POST request is sent to `data-url`
 * with the current query. Arrow keys and Enter navigate and select suggestions;
 * Escape closes the dropdown.
 *
 * @module search-query
 */
import { defineFeature } from "../utils/define-feature";
import { setSearchQueryEventListeners } from "../utils/search-query-listeners";

export default defineFeature((root) => {
    setSearchQueryEventListeners(root);
});

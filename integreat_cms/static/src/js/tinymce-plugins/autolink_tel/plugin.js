/**
 * This is a fork of the original autolink plugin of the TinyMCE (see: https://github.com/tinymce/tinymce-dist/), which is licensed under the LGPL.
 *
 * The changes are aiming to add an automatic detection of phone numbers with the specific pattern of a leading zero and at least 5 more digits
 * that might be separated by a slash.
 *
 * Author of the changes: Jan-Ulrich Holtgrave (holtgrave@integreat-app.de)
 *
 * Copyright (c) Tiny Technologies, Inc. All rights reserved.
 * Licensed under the LGPL or a commercial license.
 * For LGPL see License.txt in the project root for license information.
 * For commercial licenses see https://www.tiny.cloud/
 *
 * Version: 5.7.0 (2021-02-10)
 */
(() => {
    const global = tinymce.util.Tools.resolve("tinymce.PluginManager");

    const global$1 = tinymce.util.Tools.resolve("tinymce.Env");

    const getAutoLinkPattern = (editor) =>
        editor.getParam(
            "autolink_pattern",
            /^(https?:\/\/|ssh:\/\/|ftp:\/\/|file:\/|www\.|(?:mailto:)?[A-Z0-9._%+-]+@(?!.*@))(.+)$/i
        );
    const getDefaultLinkTarget = (editor) => editor.getParam("default_link_target", false);
    const getDefaultLinkProtocol = (editor) => editor.getParam("link_default_protocol", "http", "string");

    // constant values and magic numbers used below
    const CHAR_CODE_SPACE = 160;
    const NODE_TYPE_ELEMENT = 1;
    const NODE_TYPE_TEXT = 3;
    const MIN_RANGE_THRESHOLD = 5;

    const rangeEqualsDelimiterOrSpace = (rangeString, delimiter) =>
        rangeString === delimiter || rangeString === " " || rangeString.charCodeAt(0) === CHAR_CODE_SPACE;
    const scopeIndex = (container, idx) => {
        let index = idx < 0 ? 0 : idx;
        if (container.nodeType === NODE_TYPE_TEXT) {
            const len = container.data.length;
            if (index > len) {
                index = len;
            }
        }
        return index;
    };
    const setStart = (rng, container, offset) => {
        if (container.nodeType !== NODE_TYPE_ELEMENT || container.hasChildNodes()) {
            rng.setStart(container, scopeIndex(container, offset));
        } else {
            rng.setStartBefore(container);
        }
    };
    const setEnd = (rng, container, offset) => {
        if (container.nodeType !== NODE_TYPE_ELEMENT || container.hasChildNodes()) {
            rng.setEnd(container, scopeIndex(container, offset));
        } else {
            rng.setEndAfter(container);
        }
    };
    const parseCurrentLine = (editor, endOffset, delimiter) => {
        let end;
        let endContainer;
        let bookmark;
        let text;
        let prev;
        let len;
        let rngText;
        const autoLinkPattern = getAutoLinkPattern(editor);
        const defaultLinkTarget = getDefaultLinkTarget(editor);
        if (editor.selection.getNode().tagName === "A") {
            return;
        }
        const rng = editor.selection.getRng().cloneRange();
        if (rng.startOffset < MIN_RANGE_THRESHOLD) {
            prev = rng.endContainer.previousSibling;
            if (!prev) {
                if (!rng.endContainer.firstChild || !rng.endContainer.firstChild.nextSibling) {
                    return;
                }
                prev = rng.endContainer.firstChild.nextSibling;
            }
            len = prev.length;
            setStart(rng, prev, len);
            setEnd(rng, prev, len);
            if (rng.endOffset < MIN_RANGE_THRESHOLD) {
                return;
            }
            end = rng.endOffset;
            endContainer = prev;
        } else {
            endContainer = rng.endContainer;
            if (endContainer.nodeType !== NODE_TYPE_TEXT && endContainer.firstChild) {
                while (endContainer.nodeType !== NODE_TYPE_TEXT && endContainer.firstChild) {
                    endContainer = endContainer.firstChild;
                }
                if (endContainer.nodeType === NODE_TYPE_TEXT) {
                    setStart(rng, endContainer, 0);
                    setEnd(rng, endContainer, endContainer.nodeValue.length);
                }
            }
            if (rng.endOffset === 1) {
                /* eslint-disable-next-line no-magic-numbers */
                end = 2;
            } else {
                end = rng.endOffset - 1 - endOffset;
            }
        }
        const start = end;
        do {
            /* eslint-disable-next-line no-magic-numbers */
            setStart(rng, endContainer, end >= 2 ? end - 2 : 0);
            setEnd(rng, endContainer, end >= 1 ? end - 1 : 0);
            end -= 1;
            rngText = rng.toString();
        } while (
            rngText !== " " &&
            rngText !== "" &&
            rngText.charCodeAt(0) !== CHAR_CODE_SPACE &&
            /* eslint-disable-next-line no-magic-numbers */
            end - 2 >= 0 &&
            rngText !== delimiter
        );
        if (rangeEqualsDelimiterOrSpace(rng.toString(), delimiter)) {
            setStart(rng, endContainer, end);
            setEnd(rng, endContainer, start);
            end += 1;
        } else if (rng.startOffset === 0) {
            setStart(rng, endContainer, 0);
            setEnd(rng, endContainer, start);
        } else {
            setStart(rng, endContainer, end);
            setEnd(rng, endContainer, start);
        }
        text = rng.toString();
        if (text.charAt(text.length - 1) === ".") {
            setEnd(rng, endContainer, start - 1);
        }
        text = rng.toString().trim();
        const matches = text.match(autoLinkPattern);
        const phoneMatches = text.match("(0[0-9/]{6,20})");
        const protocol = getDefaultLinkProtocol(editor);
        if (matches) {
            if (matches[1] === "www.") {
                matches[1] = `${protocol}://www.`;
            } else if (/@$/.test(matches[1]) && !/^mailto:/.test(matches[1])) {
                matches[1] = `mailto:${matches[1]}`;
            }
            bookmark = editor.selection.getBookmark();
            editor.selection.setRng(rng);
            editor.execCommand("createlink", false, matches[1] + matches[2]);
            if (defaultLinkTarget !== false) {
                editor.dom.setAttrib(editor.selection.getNode(), "target", defaultLinkTarget);
            }
            editor.selection.moveToBookmark(bookmark);
            editor.nodeChanged();
        } else if (phoneMatches) {
            phoneMatches[1] = `tel:${phoneMatches[1]}`;
            bookmark = editor.selection.getBookmark();
            editor.selection.setRng(rng);
            editor.execCommand("createlink", false, phoneMatches[1]);
            if (defaultLinkTarget !== false) {
                editor.dom.setAttrib(editor.selection.getNode(), "target", defaultLinkTarget);
            }
            editor.selection.moveToBookmark(bookmark);
            editor.nodeChanged();
        }
    };
    const handleEclipse = (editor) => {
        parseCurrentLine(editor, -1, "(");
    };
    const handleSpacebar = (editor) => {
        parseCurrentLine(editor, 0, "");
    };
    const handleEnter = (editor) => {
        parseCurrentLine(editor, -1, "");
    };
    const setup = (editor) => {
        const KEY_CODE_ENTER = 13;
        const KEY_CODE_SPACE = 32;
        const KEY_CODE_SELECT = 41;

        let autoUrlDetectState;
        /* eslint-disable-next-line consistent-return */
        editor.on("keydown", (e) => {
            if (e.keyCode === KEY_CODE_ENTER) {
                return handleEnter(editor);
            }
        });
        if (global$1.browser.isIE()) {
            editor.on("focus", () => {
                if (!autoUrlDetectState) {
                    autoUrlDetectState = true;
                    try {
                        editor.execCommand("AutoUrlDetect", false, true);
                    } catch (ex) {}
                }
            });
            return "";
        }
        /* eslint-disable-next-line consistent-return */
        editor.on("keypress", (e) => {
            if (e.keyCode === KEY_CODE_SELECT) {
                return handleEclipse(editor);
            }
        });
        /* eslint-disable-next-line consistent-return */
        editor.on("keyup", (e) => {
            if (e.keyCode === KEY_CODE_SPACE) {
                return handleSpacebar(editor);
            }
        });
        return "";
    };

    const Plugin = () => {
        global.add("autolink_tel", (editor) => {
            setup(editor);
        });
    };

    Plugin();
})();

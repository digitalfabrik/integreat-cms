import { getCsrfToken } from "../../utils/csrf-token";

(() => {
    const tinymceConfig = document.getElementById("tinymce-config-options");

    const getCompletions = async (query, id) => {
        const url = tinymceConfig.getAttribute("data-link-ajax-url");
        const response = await fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({
                query_string: query,
                object_types: ["event", "page", "poi"],
                archived: false,
            }),
        });
        const HTTP_STATUS_OK = 200;
        if (response.status !== HTTP_STATUS_OK) {
            return [];
        }

        const data = await response.json();
        return [data.data, id];
    };

    // Checks if the url is likely missing the https:// prefix and add it if that is the case
    const checkUrlHttps = (url) => {
        // This regex matches domains without protocol (strings which contain a dot without a preceding colon or slash)
        const re = /^[^:/]+[.].+/;
        if (re.test(url)) {
            return `https://${url}`;
        }
        return url;
    };

    const updateLink = (editor, anchorElm, text, linkAttrs) => {
        if (text !== null) {
            /* eslint-disable-next-line no-param-reassign */
            anchorElm.textContent = text;
        }

        editor.dom.setAttribs(anchorElm, linkAttrs);
        editor.selection.select(anchorElm);
    };

    tinymce.PluginManager.add("custom_link_input", (editor, _url) => {
        const isAnchor = (node) => node.nodeName.toLowerCase() === "a" && node.href;
        const getAnchor = () => {
            let node = editor.selection.getNode();
            while (node !== null) {
                if (isAnchor(node)) {
                    return node;
                }
                node = node.parentNode;
            }
            return null;
        };

        const openDialog = () => {
            const anchor = getAnchor();
            const initialText = anchor ? anchor.textContent : editor.selection.getContent({ format: "text" });
            const initialUrl = anchor ? anchor.getAttribute("href") : "";
            const initialAutoUpdateValue = anchor ? anchor.getAttribute("data-integreat-auto-update") === "true" : true;

            const textDisabled = anchor ? anchor.children.length > 0 : false;
            let prevSearchText = "";
            let prevLinkUrl = initialUrl;
            let prevSelectedCompletion = "";

            // Store the custom user data separately, so that they can be restored when required
            const userData = { url: "", text: "" };

            // Stores the current request id, so that outdated requests get ignored
            let ajaxRequestId = 0;
            const defaultCompletionItem = {
                text: tinymceConfig.getAttribute("data-link-no-results-text"),
                title: "",
                value: "",
            };
            const completionItems = [defaultCompletionItem];
            let currentCompletionText = "";

            const updateDialog = (api) => {
                let data = api.getData();

                let urlChangedBySearch = false;
                // Check if the selected completion changed
                if (prevSelectedCompletion !== data.completions) {
                    // find the correct text currently shown in the completion items box
                    if (completionItems.length > 0) {
                        const currentCompletion = completionItems.find(
                            (completion) => completion.value === data.completions
                        );
                        // Don't set the completion text to `- no results -`
                        if (currentCompletion.value !== "") {
                            currentCompletionText = currentCompletion.title;
                        } else {
                            currentCompletionText = "";
                        }
                    } else {
                        currentCompletionText = "";
                    }

                    // Set the url either to the selected internal link or to the user link
                    if (data.completions !== "") {
                        urlChangedBySearch = true;
                        api.setData({ url: data.completions });
                        // if the text is not defined by the user, set it to the current completion item
                        if (!data.text || (userData.text !== data.text && !textDisabled)) {
                            api.setData({ text: currentCompletionText });
                        }
                    } else {
                        // restore the original user data
                        api.setData({
                            url: userData.url,
                            text: textDisabled ? "" : userData.text,
                        });
                    }
                }
                prevSelectedCompletion = data.completions;

                // Automatically update the text input to the url by default
                data = api.getData();
                if (!textDisabled && !urlChangedBySearch && data.text === prevLinkUrl) {
                    api.setData({ text: data.url });
                }
                prevLinkUrl = data.url;

                // Update the user link
                if (data.url !== data.completions) {
                    userData.url = data.url;
                }
                if (!textDisabled && data.text !== data.url && data.text !== currentCompletionText) {
                    userData.text = data.text;
                }

                // Disable the submit button if either one of the url or text are empty
                data = api.getData();
                if (data.url.trim() && (textDisabled || data.text.trim())) {
                    api.enable("submit");
                } else {
                    api.disable("submit");
                }

                // make new ajax request on user input
                if (data.search !== prevSearchText && data.search !== "") {
                    ajaxRequestId += 1;
                    getCompletions(data.search, ajaxRequestId).then(([newCompletions, requestId]) => {
                        if (requestId !== ajaxRequestId) {
                            return;
                        }

                        completionItems.length = 0;
                        for (const completion of newCompletions) {
                            completionItems.push({
                                text: completion.path,
                                title: completion.html_title,
                                value: completion.url,
                            });
                        }

                        let completionDisabled = false;
                        if (completionItems.length === 0) {
                            completionDisabled = true;
                            completionItems.push(defaultCompletionItem);
                        }

                        // It seems like there is no better way to update the completion list
                        /* eslint-disable-next-line @typescript-eslint/no-use-before-define */
                        api.redial(dialogConfig);
                        api.setData(data);
                        api.focus("search");
                        prevSearchText = data.search;

                        if (completionDisabled) {
                            api.disable("completions");
                        } else {
                            api.enable("completions");
                        }

                        updateDialog(api);
                    });
                } else if (data.search === "" && prevSearchText !== "") {
                    // force an update so that the original user url can get restored
                    completionItems.length = 0;
                    completionItems.push(defaultCompletionItem);
                    /* eslint-disable-next-line @typescript-eslint/no-use-before-define */
                    api.redial(dialogConfig);
                    api.setData(data);
                    api.focus("search");
                    prevSearchText = data.search;
                    api.disable("completions");
                    updateDialog(api);
                }
            };

            const dialogConfig = {
                title: tinymceConfig.getAttribute("data-link-dialog-title-text"),
                body: {
                    type: "panel",
                    items: [
                        {
                            type: "input",
                            name: "url",
                            label: tinymceConfig.getAttribute("data-link-dialog-url-text"),
                        },
                        {
                            type: "input",
                            name: "text",
                            label: tinymceConfig.getAttribute("data-link-dialog-text-text"),
                            disabled: textDisabled,
                        },
                        {
                            type: "label",
                            label: tinymceConfig.getAttribute("data-link-dialog-internal_link-text"),
                            items: [
                                {
                                    type: "input",
                                    name: "search",
                                },
                                {
                                    type: "selectbox",
                                    name: "completions",
                                    items: completionItems,
                                    disabled: true,
                                },
                                {
                                    type: "checkbox",
                                    name: "autoupdate",
                                    label: tinymceConfig.getAttribute("data-link-dialog-autoupdate-text"),
                                },
                            ],
                        },
                    ],
                },
                buttons: [
                    {
                        type: "cancel",
                        text: tinymceConfig.getAttribute("data-dialog-cancel-text"),
                    },
                    {
                        type: "submit",
                        name: "submit",
                        text: tinymceConfig.getAttribute("data-dialog-submit-text"),
                        primary: true,
                        disabled: true,
                    },
                ],
                initialData: {
                    text: initialText,
                    url: initialUrl,
                    autoupdate: initialAutoUpdateValue,
                },
                onSubmit: (api) => {
                    const data = api.getData();
                    const { url, autoupdate } = data;
                    const text = textDisabled ? null : data.text || url;

                    if (data.url.trim() === "") {
                        return;
                    }
                    api.close();

                    const realUrl = checkUrlHttps(url);

                    // Either insert a new link or update the existing one
                    const anchor = getAnchor();
                    if (!anchor) {
                        editor.insertContent(`<a href=${realUrl} data-integreat-auto-update=${autoupdate}>${text}</a>`);
                    } else {
                        updateLink(editor, anchor, text, {
                            "href": realUrl,
                            "data-integreat-auto-update": autoupdate,
                        });
                    }
                },
                onChange: updateDialog,
            };

            return editor.windowManager.open(dialogConfig);
        };

        editor.addShortcut("Meta+K", tinymceConfig.getAttribute("data-link-menu-text"), openDialog);

        editor.ui.registry.addMenuItem("add_link", {
            text: tinymceConfig.getAttribute("data-link-menu-text"),
            icon: "link",
            shortcut: "Meta+K",
            onAction: openDialog,
        });

        // This form opens when a link is current selected with the cursor
        editor.ui.registry.addContextForm("link_context_form", {
            predicate: isAnchor,
            initValue: () => {
                const elm = getAnchor();
                return elm ? elm.href : "";
            },
            position: "node",
            commands: [
                {
                    type: "contextformbutton",
                    icon: "link",
                    tooltip: tinymceConfig.getAttribute("data-update-text"),
                    primary: true,
                    onSetup: (buttonApi) => {
                        const nodeChangeHandler = () => {
                            buttonApi.setDisabled(editor.readonly);
                        };
                        editor.on("nodechange", nodeChangeHandler);
                        return () => {
                            editor.off("nodechange", nodeChangeHandler);
                        };
                    },
                    onAction: (formApi) => {
                        const url = formApi.getValue();
                        if (url) {
                            const realUrl = checkUrlHttps(url);
                            const anchor = getAnchor();
                            updateLink(editor, anchor, null, {
                                href: realUrl,
                            });
                        }
                        formApi.hide();
                    },
                },
                {
                    type: "contextformbutton",
                    icon: "unlink",
                    tooltip: tinymceConfig.getAttribute("data-link-remove-text"),
                    active: false,
                    onAction: (formApi) => {
                        const elm = getAnchor();
                        if (elm) {
                            elm.insertAdjacentHTML("beforebegin", elm.innerHTML);
                            elm.remove();
                        }
                        formApi.hide();
                    },
                },
                {
                    type: "contextformbutton",
                    icon: "new-tab",
                    tooltip: tinymceConfig.getAttribute("data-link-open-text"),
                    active: false,
                    onAction: () => {
                        const elm = getAnchor();
                        if (elm) {
                            window.open(elm.getAttribute("href"), "_blank");
                        }
                    },
                },
            ],
        });

        return {};
    });
})();

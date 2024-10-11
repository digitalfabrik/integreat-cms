import { getCsrfToken } from "../../utils/csrf-token";

(() => {
    const tinymceConfig = document.getElementById("tinymce-config-options");

    const contactUrlRegex = new RegExp(tinymceConfig.getAttribute("data-contact-url-regex"));

    const seenContacts = {};

    const cacheContact = (contact) => {
        if (contact && contact.id) {
            seenContacts[contact.id] = contact;
        }
    };
    const getCachedContact = (id) => {
        if (id && id in seenContacts) {
            return seenContacts[id];
        }
        return null;
    };

    const getCompletions = async (query, id) => {
        const url = tinymceConfig.getAttribute("data-contact-ajax-url");

        const response = await fetch(url, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({
                query_string: query,
                object_types: ["contact"],
                archived: false,
            }),
        });
        const HTTP_STATUS_OK = 200;
        if (response.status !== HTTP_STATUS_OK) {
            return [];
        }

        const data = await response.json();

        const normalizeString = (s) => s.trim().replaceAll(/\s+/g, " ").toLowerCase();

        const normalizedQuery = normalizeString(query);

        const longestCommonSublist = (a, b) => {
            const maxLength = Math.min(a.length, b.length);
            let longestFoundMatch = null;
            let foundMatchLength = 0;
            const areListsEqual = (listA, listB) => {
                if (listA.length !== listB.length) {
                    return false;
                }
                for (let i = 0; i < listA.length; i++) {
                    if (listA[i] !== listB[i]) {
                        return false;
                    }
                }
                return true;
            };
            const getRealLength = (list) => list.reduce((acc, x) => acc + x.length, list.length - 1);
            for (let len = maxLength; len > 0; len--) {
                for (let i = 0; i <= a.length - len; i++) {
                    const subA = a.slice(i, i + len);
                    const realLength = getRealLength(subA);
                    // Don't bother if we won't get a better result anyway
                    if (longestFoundMatch === null || realLength > foundMatchLength) {
                        for (let j = 0; j <= b.length - len; j++) {
                            const subB = b.slice(j, j + len);
                            if (areListsEqual(subA, subB)) {
                                longestFoundMatch = subA.join(" ");
                                foundMatchLength = realLength;
                            }
                        }
                    }
                }
                // If we already found a match, naively we could abort here
                // but since individual words might be much longer than others,
                // that is a false conclusion that will produce bugs
                // if (longestFoundMatch !== null)  return longestFoundMatch;
            }
            return longestFoundMatch;
        };
        const longestCommonSubstring = (a, b) => longestCommonSublist(a.split(" "), b.split(" "));

        const searchableFields = ["point_of_contact_for", "name", "email", "phone_number", "website"];
        // Figure out how relevant each result is
        const values = data.data.map((e) => {
            const fieldContibutions = searchableFields.map((field) => {
                // Find longest common substring between the field and the original query
                const lcs = longestCommonSubstring(normalizeString(e[field]), normalizedQuery);
                if (lcs === null) {
                    return 0;
                }
                // Square the length so longer matches in only a few fields get a much higher value than many short matches all over
                return lcs.length ** 2;
            });
            e.matchScore = fieldContibutions.reduce((a, b) => a + b);
            return e;
        });
        values.sort((a, b) => b.matchScore - a.matchScore);

        return [values, id];
    };

    const renderContactLine = (contact) => {
        const point_of_contact_for = contact.point_of_contact_for && contact.point_of_contact_for.trim() !== "" ? `${contact.point_of_contact_for.trim()}: ` : "";
        const name = contact.name && contact.name.trim() !== "" ? contact.name.trim() : "";
        const details = ["email", "phone_number", "website"].map((k) => contact[k]).filter((e) => e && e.trim() !== "");
        return `${point_of_contact_for}${name} (${details.join(", ")})`;
    };

    const notranslate = (html) => `<span class="notranslate" dir="ltr" translate="no">${html}</span>`;

    const updateContact = (editor, id, elm) => {
        const contact = getCachedContact(id) || {};
        const url = contact && contact.url ? contact.url : "";
        const marker = `<a href="${url}" style="opacity: 0; position: absolute; font-size: 0;">Contact</a>`;

        const point_of_contact_for = contact && contact.point_of_contact_for && contact.point_of_contact_for.trim() !== "" ? `${contact.point_of_contact_for.trim()}: ` : "";
        const name = contact && contact.name && contact.name.trim() !== "" ? notranslate(contact.name.trim()) : "";
        const email =
            contact && contact.email && contact.email.trim() !== ""
                ? `<p><img style="width: 15px; height: 15px;" src="${tinymceConfig.getAttribute(`data-email-icon-src`)}" alt="Email"> <a href="mailto:${contact.email.trim()}">${notranslate(contact.email.trim())}</a></p>`
                : "";
        const phoneNumber =
            contact && contact.phone_number && contact.phone_number.trim() !== ""
                ? `<p><img style="width: 15px; height: 15px;" src="${tinymceConfig.getAttribute(`data-call-icon-src`)}" alt="Phone Number"> <a href="tel:${contact.phone_number.trim()}">${notranslate(contact.phone_number.trim())}</a></p>`
                : "";
        const website =
            contact && contact.website && contact.website.trim() !== ""
                ? `<p><img style="width: 15px; height: 15px;" src="${tinymceConfig.getAttribute(`data-www-icon-src`)}" alt="Website"> <a href="${contact.website.trim()}">${notranslate(contact.website.trim())}</a></p>`
                : "";
        const innerHTML = `
            <h4>${point_of_contact_for}${name}</h4>
            ${email}
            ${phoneNumber}
            ${website}
        `;
        if (elm) {
            elm.innerHTML = `${marker}${innerHTML}`;
            editor.selection.select(elm);
        }
        const styles = [
            "display: inline-block;",
            "box-sizing: border-box;",
            "min-width: 50%;",
            "padding: 0.1em 1em;",
            "border-radius: 0.3em;",
            "background: rgba(127, 127, 127, 0.25);",
            "outline: 4px solid #b4ffff !important;",
            "cursor: default !important;",
            "color: initial;",
            "text-decoration: initial;",
        ].join(" ");
        return `<div contenteditable="false" style="${styles}">${marker}${innerHTML}</div>`;
    };

    tinymce.PluginManager.add("custom_contact_input", (editor, _url) => {
        const isContact = (node) =>
            node.nodeName.toLowerCase() === "div" &&
            node.children.length > 0 &&
            node.children[0].nodeName.toLowerCase() === "a" &&
            node.children[0].getAttribute("href").match(contactUrlRegex);
        const getContact = () => {
            let node = editor.selection.getNode();
            while (node !== null) {
                if (isContact(node)) {
                    return node;
                }
                node = node.parentNode;
            }
            return null;
        };

        const openDialog = () => {
            const contact = getContact();
            const match = contact ? contact.children[0].getAttribute("href").match(contactUrlRegex) : null;
            const initialId = match && match[2] ? match[2] : "";

            let prevSearchText = "";
            let prevSelectedCompletion = "";

            // Store the custom user data separately, so that they can be restored when required
            const userData = { id: "" };

            // Stores the current request id, so that outdated requests get ignored
            let ajaxRequestId = 0;
            const defaultCompletionItem = {
                text: tinymceConfig.getAttribute("data-contact-no-results-text"),
                title: "",
                value: "",
            };
            const completionItems = [defaultCompletionItem];

            const updateDialog = (api) => {
                let data = api.getData();

                // Check if the selected completion changed
                if (prevSelectedCompletion !== data.completions) {
                    // Set the url either to the selected internal link or to the user link
                    if (data.completions !== "") {
                        api.setData({
                            id: data.completions,
                        });
                    } else {
                        // restore the original user data
                        api.setData({
                            id: userData.id,
                        });
                    }
                }
                prevSelectedCompletion = data.completions;

                // Update the user link
                if (data.id !== data.completions) {
                    userData.id = data.id;
                }

                // Disable the submit button if either one of the url or text are empty
                data = api.getData();
                if (data.id.trim()) {
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
                                text: renderContactLine(completion),
                                title: completion.html_title,
                                value: `${completion.id}`,
                            });
                            cacheContact(completion);
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
                title: tinymceConfig.getAttribute("data-contact-dialog-title-text"),
                body: {
                    type: "panel",
                    items: [
                        {
                            type: "label",
                            label: tinymceConfig.getAttribute("data-contact-dialog-search-text"),
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
                            ],
                        },
                        {
                            type: "input",
                            name: "id",
                            label: tinymceConfig.getAttribute("data-contact-dialog-id-text"),
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
                    id: initialId,
                },
                onSubmit: (api) => {
                    const data = api.getData();
                    const { id } = data;

                    if (data.id.trim() === "") {
                        return;
                    }
                    api.close();

                    // Either insert a new link or update the existing one
                    const contact = getContact();
                    const html = updateContact(editor, id, contact);
                    if (!contact) {
                        /* We want to insert the contact card as a new block element, even though it is wrapped in an anchor
                         * This means if we are multiple levels inside inline elements (e.g. <p><span><b><i>…),
                         * these should be split at the cursor, where the contact should be inserted.
                         * Surprisingly, just inserting a div achieves this –
                         * probably because it is a block element, while an anchor (<a>) is not.
                         */
                        editor.insertContent('<div data-bogus-split="5"></div>');

                        const elm = editor.$("div[data-bogus-split=5]")[0];
                        // If TinyMCEs behaviour changes in the future, it might become necessary to split manually similar to this:
                        /*
                        const selectedNode = editor.selection.getNode();
                        if (!editor.dom.isBlock(selectedNode)) {
                            let node = selectedNode;
                            while (!editor.dom.isBlock(node)) {
                                node = node.parentElement;
                            }
                            editor.dom.split(node, elm);
                        }
                        */
                        // Finally, we can replace the split marker element with the actual contact card
                        elm.outerHTML = html;
                    }
                },
                onChange: updateDialog,
            };

            return editor.windowManager.open(dialogConfig);
        };

        // editor.addShortcut("Meta+C", tinymceConfig.getAttribute("data-contact-menu-text"), openDialog);

        editor.ui.registry.addMenuItem("add_contact", {
            text: tinymceConfig.getAttribute("data-contact-menu-text"),
            icon: "contact",
            // shortcut: "Meta+C",
            onAction: openDialog,
        });

        editor.ui.registry.addButton("change_contact", {
            text: tinymceConfig.getAttribute("data-contact-change-text"),
            icon: "contact",
            onAction: openDialog,
        });

        editor.ui.registry.addButton("remove_contact", {
            text: tinymceConfig.getAttribute("data-contact-remove-text"),
            icon: "remove",
            onAction: () => {
                const contact = getContact();
                if (contact) {
                    contact.remove();
                }
            },
        });

        // This form opens when a link is current selected with the cursor
        editor.ui.registry.addContextToolbar("contact_context_toolbar", {
            predicate: isContact,
            position: "node",
            scope: "node",
            items: "change_contact remove_contact",
        });

        return {};
    });
})();

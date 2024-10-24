import { getCsrfToken } from "../../utils/csrf-token";

(() => {
    const tinymceConfig = document.getElementById("tinymce-config-options");

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
                if (listA.length != listB.length) return false;
                for (let i = 0; i < listA.length; i++) {
                    if (listA[i] != listB[i]) return false;
                }
                return true;
            };
            const getRealLength = (list) => {
                return list.reduce((acc, x) => acc + x.length, list.length - 1);
            };
            for (let len = maxLength; len > 0; len--) {
                for (let i = 0; i <= a.length - len; i++) {
                    const subA = a.slice(i, i + len);
                    const realLength = getRealLength(subA);
                    if (longestFoundMatch !== null && realLength <= foundMatchLength) {
                        // Don't bother if we won't get a better result anyway
                        continue;
                    }
                    for (let j = 0; j <= b.length - len; j++) {
                        const subB = b.slice(j, j + len);
                        if (areListsEqual(subA, subB)) {
                            longestFoundMatch = subA.join(" ");
                            foundMatchLength = realLength;
                        }
                    }
                }
                // If we already found a match, naively we could abort here
                // but since individual words might be much longer than others,
                // that is a false conclusion that will produce bugs
                //if (longestFoundMatch !== null)  return longestFoundMatch;
            }
            return longestFoundMatch;
        };
        const longestCommonSubstring = (a, b) => longestCommonSublist(a.split(" "), b.split(" "));

        const searchableFields = ["title", "name", "email", "phone_number", "website"];
        // Figure out how relevant each result is
        const values = data.data.map((e) => {
            const fieldContibutions = searchableFields.map((field) => {
                // Find longest common substring between the field and the original query
                const lcs = longestCommonSubstring(normalizeString(e[field]), normalizedQuery);
                if (lcs === null) return 0;
                // Square the length so longer matches in only a few fields get a much higher value than many short matches all over
                return lcs.length ** 2;
            });
            e._matchScore = fieldContibutions.reduce((a, b) => a + b);
            return e;
        });
        values.sort((a, b) => b._matchScore - a._matchScore);

        return [values, id];
    };

    const renderContactLine = (contact) => {
        const title = contact.title && contact.title.trim() !== "" ? `${contact.title.trim()}: ` : "";
        const name = contact.name && contact.name.trim() !== "" ? contact.name.trim() : "";
        const details = ["email", "phone_number", "website"].map((k) => contact[k]).filter((e) => e && e.trim() !== "");
        return `${title}${name} (${details.join(", ")})`;
    };

    const updateContact = (editor, id, elm) => {
        const contact = getCachedContact(id) || {};
        const title = contact && contact.title && contact.title.trim() !== "" ? `${contact.title.trim()}: ` : "";
        const name = contact && contact.name && contact.name.trim() !== "" ? contact.name.trim() : "";
        const email =
            contact && contact.email && contact.email.trim() !== ""
                ? `<p><img style="width: 15px; height: 15px;" src="${tinymceConfig.getAttribute(`data-email-icon-src`)}" alt="Email"> ${contact.email.trim()}</p>`
                : "";
        const phone_number =
            contact && contact.phone_number && contact.phone_number.trim() !== ""
                ? `<p><img style="width: 15px; height: 15px;" src="${tinymceConfig.getAttribute(`data-call-icon-src`)}" alt="Phone Number"> ${contact.phone_number.trim()}</p>`
                : "";
        const website =
            contact && contact.website && contact.website.trim() !== ""
                ? `<p><img style="width: 15px; height: 15px;" src="${tinymceConfig.getAttribute(`data-www-icon-src`)}" alt="Website"> ${contact.website.trim()}</p>`
                : "";
        const innerHTML = `
            <h4>${title}${name}</h4>
            ${email}
            ${phone_number}
            ${website}
        `;
        if (elm) {
            elm.dataset.contact = id;
            elm.innerHTML = innerHTML;
            editor.selection.select(elm);
        }
        return `<div data-contact="${id}" contenteditable="false">${innerHTML}</div>`;
    };

    tinymce.PluginManager.add("custom_contact_input", (editor, _url) => {
        const isContact = (node) => node.nodeName.toLowerCase() === "div" && "contact" in node.dataset;
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
            const initialId = contact ? contact.getAttribute("data-contact") : "";

            let prevSearchText = "";
            let prevContactId = initialId;
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
            let currentCompletionText = "";

            const updateDialog = (api) => {
                let data = api.getData();

                let idChangedBySearch = false;
                // Check if the selected completion changed
                if (prevSelectedCompletion !== data.completions) {
                    // find the correct text currently shown in the completion items box
                    if (completionItems.length > 0) {
                        const currentCompletion = completionItems.find(
                            (completion) => completion.value === data.completions
                        );
                        // Don't set the completion text to `- no results -`
                        if (currentCompletion.value !== "") {
                            currentCompletionText = renderContactLine(currentCompletion);
                            prevContactId = currentCompletion.id;
                        }
                    }

                    // Set the url either to the selected internal link or to the user link
                    if (data.completions !== "") {
                        idChangedBySearch = true;
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
                        editor.insertContent(html);
                    }
                },
                onChange: updateDialog,
            };

            return editor.windowManager.open(dialogConfig);
        };

        //editor.addShortcut("Meta+C", tinymceConfig.getAttribute("data-contact-menu-text"), openDialog);

        editor.ui.registry.addMenuItem("add_contact", {
            text: tinymceConfig.getAttribute("data-contact-menu-text"),
            icon: "contact",
            //shortcut: "Meta+C",
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

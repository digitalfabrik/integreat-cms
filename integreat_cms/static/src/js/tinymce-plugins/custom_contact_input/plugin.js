import TomSelect from "tom-select";
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

    const getCompletions = async (query) => {
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

        return data.data;
    };

    const renderContactLine = (contact) => {
        const point_of_contact_for = contact.point_of_contact_for && contact.point_of_contact_for.trim() !== "" ? `${contact.point_of_contact_for.trim()}: ` : "";
        const name = contact.name && contact.name.trim() !== "" ? contact.name.trim() : "";
        const details = ["email", "phone_number", "website"].map((k) => contact[k]).filter((e) => e && e.trim() !== "");
        return `${point_of_contact_for}${name} (${details.join(", ")})`;
    };

    const renderSegmentedContactLine = (contact, escape) => {
        const point_of_contact_for =
            contact.point_of_contact_for && contact.point_of_contact_for.trim() !== ""
                ? `<span class="point_of_contact_for">${escape(contact.point_of_contact_for.trim())}</span>: `
                : "";
        const name =
            contact.name && contact.name.trim() !== ""
                ? `<span class="name">${escape(contact.name.trim())}</span>`
                : "";
        const details = ["email", "phone_number", "website"].reduce((list, k) => {
            const value = contact[k];
            if (value && value.trim() !== "") {
                list.push(`<span class="detail ${k}">${escape(value.trim())}</span>`);
            }
            return list;
        }, []);
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
            "background: rgba(127, 127, 127, 0.15);",
            "box-shadow: 0 .1em .1em rgba(0,0,0,0.4);",
            "cursor: default !important;",
            "color: initial;",
            "text-decoration: initial;",
            `background-image: linear-gradient(to right, rgba(255,255,255,0.9) 0 100%), url(${tinymceConfig.getAttribute(`data-contact-icon-src`)}) !important;`,
            "background-blend-mode: difference;",
            "background-position: calc(100% + 2em) calc(100% + 1em);",
            "background-size: 7em;",
            "background-repeat: no-repeat;",
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

        let tomSelectInstance;

        const openDialog = () => {
            const contact = getContact();
            const match = contact ? contact.children[0].getAttribute("href").match(contactUrlRegex) : null;
            const initialId = match && match[2] ? match[2] : "";

            const dialogConfig = {
                title: tinymceConfig.getAttribute("data-contact-dialog-title-text"),
                body: {
                    type: "panel",
                    items: [
                        {
                            type: "htmlpanel",
                            // TinyMCE only gives internal identifies, not useful ones on the generated Elements
                            //  so we have to do with an htmlpanel and initializing TomSelect separately
                            html: `<select id="completions" name="completions">`,
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
                    },
                ],
                initialData: {
                    id: initialId,
                },
                onClose: () => {
                    // Destroy TomSelect instance to avoid memory leaks
                    if (tomSelectInstance) {
                        tomSelectInstance.destroy();
                        tomSelectInstance = null;
                    }
                },
                onSubmit: (api) => {
                    // Either insert a new link or update the existing one
                    const contact = getContact();
                    const id = tomSelectInstance.getValue();

                    if (!id) {
                        return;
                    }
                    api.close();
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
            };

            setTimeout(() => {
                // Get the select and submit elements after TinyMCE rendered them
                const selectElement = document.getElementById("completions");
                const submitElement = document.querySelector(
                    ".tox-dialog:has(#completions) .tox-dialog__footer .tox-button:not(.tox-button--secondary)"
                );
                const setSubmitDisableStatus = function (value) {
                    if (submitElement) {
                        submitElement.disabled = !value;
                    }
                };

                // Initialize TomSelect on the select element
                tomSelectInstance = new TomSelect(selectElement, {
                    valueField: "id",
                    //labelField: "text", // By which field the object should be represented. We define a custom render function, so we don't need it
                    searchField: ["point_of_contact_for", "name", "email", "phone_number", "website"],
                    items: [initialId],
                    placeholder: tinymceConfig.getAttribute("data-contact-dialog-search-text"),
                    options: Object.values(seenContacts), // Initially empty, will populate with API response
                    create: false, // Users cannot just inline create contacts here
                    loadThrottle: 300, // How many ms to wait for more input before actually sending a request
                    preload: true, // Call load() once with empty query on initialization. This fetches the contact so the details are up to date
                    onInitialize: function () {
                        selectElement.classList.add("hidden");
                        this.control_input.parentElement.classList.add("tox-textfield");
                        setSubmitDisableStatus(this.getValue());
                    },
                    load: function (query, callback) {
                        if (!typeof query === "string" || query === "") {
                            /* This is dirty and shouldn't be done this way,
                               but it's just so convenient to use as a fallback
                               when we only remember the id we last set.
                               (We technically know more, but we cannot be sure it's still recent)
                             */
                            query = parseInt(this.getValue() || initialId);
                        }
                        getCompletions(query).then((newCompletions) => {
                            newCompletions.forEach(cacheContact);
                            callback(newCompletions);
                            if (typeof query === "number" && newCompletions.length > 0) {
                                // Trigger preview of of initially selected value after fetching its details
                                this.setValue(query);
                            }
                        });
                    },
                    onChange: setSubmitDisableStatus,
                    render: {
                        option: (data, escape) => {
                            // How a search result should be represented
                            return `<div>${renderSegmentedContactLine(data, escape)}</div>`;
                        },
                        item: (data, escape) => {
                            // How a selected item should be represented
                            return `<div>${renderSegmentedContactLine(data, escape)}</div>`;
                        },
                        no_results: (data, escape) => {
                            // What to display when no results are found
                            return `<div class="no-results">${escape(tinymceConfig.getAttribute("data-contact-no-results-text"))}</div>`;
                        },
                    },
                });
            }, 0);

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

import TomSelect from "tom-select";
import { getCsrfToken } from "../../utils/csrf-token";

(() => {
    const tinymceConfig = document.getElementById("tinymce-config-options");
    const completionUrl = tinymceConfig.getAttribute("data-contact-ajax-url");

    const getCompletions = async (query) => {
        const response = await fetch(completionUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({ query_string: query }),
        });

        const HTTP_STATUS_OK = 200;
        if (response.status !== HTTP_STATUS_OK) {
            return [];
        }

        const data = await response.json();
        return data.data;
    };

    const getContactHtml = async (url) => {
        const response = await fetch(url, {
            method: "GET",
            headers: {
                "X-CSRFToken": getCsrfToken(),
            },
        });

        const HTTP_STATUS_OK = 200;
        if (response.status !== HTTP_STATUS_OK) {
            return "";
        }

        const data = await response.text();
        return data;
    };

    const getContactRaw = async (url) => getContactHtml(`${url}raw/`);

    tinymce.PluginManager.add("custom_contact_input", (editor, _url) => {
        const isContact = (node) => "contactId" in node.dataset;
        const getContact = () => {
            const node = editor.selection.getNode();
            if (node.dataset.contactId !== undefined) {
                return node;
            }
            return null;
        };
        const closeContextToolbar = () => {
            editor.fire("contexttoolbar-hide", {
                toolbarKey: "contact_context_toolbar",
            });
        };

        let tomSelectInstance;

        const openDialog = (_button, initialSelection) => {
            const contact = getContact();

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
                onClose: () => {
                    // Destroy TomSelect instance to avoid memory leaks
                    if (tomSelectInstance) {
                        tomSelectInstance.destroy();
                        tomSelectInstance = null;
                    }
                },
                onSubmit: (api) => {
                    const url = tomSelectInstance.getValue();

                    if (!url) {
                        return;
                    }
                    api.close();
                    getContactHtml(url).then((html) => {
                        if (!contact) {
                            editor.insertContent(html);
                        } else {
                            contact.outerHTML = html;
                        }
                    });
                },
            };

            setTimeout(() => {
                const selectElement = document.getElementById("completions");
                const submitElement = document.querySelector(
                    ".tox-dialog:has(#completions) .tox-dialog__footer .tox-button:not(.tox-button--secondary)"
                );
                const setSubmitDisableStatus = (value) => {
                    if (!submitElement) {
                        return;
                    }

                    submitElement.disabled = !value;
                    if (!submitElement.disabled) {
                        submitElement.focus();
                    }
                };

                if (initialSelection) {
                    selectElement.add(initialSelection);
                }

                tomSelectInstance = new TomSelect(selectElement, {
                    valueField: "url",
                    labelField: "name",
                    searchField: ["name"],
                    placeholder: tinymceConfig.getAttribute("data-contact-dialog-search-text"),
                    loadThrottle: 300,
                    load: (query, callback) => {
                        getCompletions(query).then((newCompletions) => {
                            callback(newCompletions);
                        });
                    },
                    onDropdownClose: setSubmitDisableStatus,
                });

                selectElement.classList.add("hidden");
                tomSelectInstance.control_input.parentElement.classList.add("tox-textfield");
                tomSelectInstance.control_input.focus();
                setSubmitDisableStatus(tomSelectInstance.getValue());
            }, 0);

            return editor.windowManager.open(dialogConfig);
        };

        editor.addShortcut("Meta+L", tinymceConfig.getAttribute("data-contact-menu-text"), openDialog);

        editor.ui.registry.addMenuItem("add_contact", {
            text: tinymceConfig.getAttribute("data-contact-menu-text"),
            icon: "contact",
            onAction: openDialog,
        });

        editor.ui.registry.addButton("change_contact", {
            text: tinymceConfig.getAttribute("data-contact-change-text"),
            icon: "contact",
            onAction: async () => {
                const contactUrl = getContact().dataset.contactUrl;
                const updatedContact = await getContactRaw(contactUrl);

                const updatedContactOption = document.createElement("option");
                updatedContactOption.value = `${contactUrl}`;
                updatedContactOption.text = updatedContact;

                openDialog(null, updatedContactOption);
                closeContextToolbar();
            },
        });

        editor.ui.registry.addButton("remove_contact", {
            text: tinymceConfig.getAttribute("data-contact-remove-text"),
            icon: "remove",
            onAction: () => {
                const contact = getContact();
                if (contact) {
                    contact.remove();
                }
                closeContextToolbar();
            },
        });

        editor.ui.registry.addContextToolbar("contact_context_toolbar", {
            predicate: isContact,
            position: "node",
            scope: "node",
            items: "change_contact remove_contact",
        });

        return {};
    });
})();

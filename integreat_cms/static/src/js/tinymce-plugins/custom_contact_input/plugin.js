import TomSelect from "tom-select";
import { getCsrfToken } from "../../utils/csrf-token";

(() => {
    const tinymceConfig = document.getElementById("tinymce-config-options");
    const isContactsEnabled = tinymceConfig.getAttribute("data-contact-module-activated") !== "False";

    const completionUrl = tinymceConfig.getAttribute("data-contact-ajax-url");
    const noEmptyContactHint = tinymceConfig.getAttribute("data-no-empty-contact-hint");
    const HTTP_STATUS_OK = 200;

    const getCompletions = async (query) => {
        const response = await fetch(completionUrl, {
            method: "POST",
            headers: {
                "X-CSRFToken": getCsrfToken(),
            },
            body: JSON.stringify({ query_string: query }),
        });

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

        if (response.status !== HTTP_STATUS_OK) {
            return "";
        }

        const data = await response.text();
        return data;
    };

    const getContactRaw = async (url) => {
        const response = await fetch(`${url.split("?")[0]}raw/`, {
            method: "GET",
            headers: {
                "X-CSRFToken": getCsrfToken(),
            },
        });

        if (response.status !== HTTP_STATUS_OK) {
            return {};
        }

        const data = await response.json();
        return data.data;
    };

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
            editor.dispatch("contexttoolbar-hide", {
                toolbarKey: "contact_context_toolbar",
            });
        };

        let tomSelectInstance;

        const openDialog = (_button, initialSelection, selectedDetails) => {
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
                        { type: "htmlpanel", html: `<div id="details-area" class="details-area"></div>` },
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
                    const details = Array.from(
                        document.getElementById("details-area").querySelectorAll('input[type="checkbox"]:checked')
                    )
                        .map((cb) => cb.value)
                        .join(",");
                    api.close();
                    getContactHtml(`${url}?details=${details}`).then((html) => {
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
                const detailsArea = document.getElementById("details-area");
                const submitElement = document.querySelector(
                    ".tox-dialog:has(#completions) .tox-dialog__footer .tox-button:not(.tox-button--secondary)"
                );
                const anyChecked = () =>
                    Array.from(document.querySelectorAll(".details-checkbox")).some((checkbox) => checkbox.checked);
                const setSubmitDisableStatus = (value) => {
                    if (!submitElement) {
                        return;
                    }

                    submitElement.disabled = !value || !anyChecked();
                    if (!submitElement.disabled) {
                        submitElement.focus();
                        submitElement.title = "";
                    } else {
                        submitElement.title = noEmptyContactHint;
                    }
                };
                const updateDetailSelection = (value) => {
                    detailsArea.innerHTML = "";

                    // removing the currently selected option calls this function with empty string
                    if (value === "") {
                        return;
                    }

                    const availableDetails = tomSelectInstance.options[value].details;

                    for (const [key, value] of Object.entries(availableDetails)) {
                        const wrapper = document.createElement("div");

                        const checkbox = document.createElement("input");
                        checkbox.type = "checkbox";
                        checkbox.classList = ["details-checkbox"];
                        checkbox.checked = selectedDetails?.includes(key) || !selectedDetails;
                        checkbox.value = key;
                        checkbox.id = key;
                        checkbox.style.border = "1px solid";
                        checkbox.style.width = "1em";
                        checkbox.style.height = "1em";
                        checkbox.style.margin = "0 5px 0 5px";
                        checkbox.style.verticalAlign = "middle";

                        const label = document.createElement("label");
                        label.htmlFor = key;
                        label.textContent = value;
                        label.style.verticalAlign = "middle";

                        wrapper.append(checkbox);
                        wrapper.append(label);
                        detailsArea.append(wrapper);

                        checkbox.addEventListener("click", () => {
                            setSubmitDisableStatus(true);
                        });
                    }
                };

                if (initialSelection) {
                    const updatedContactOption = document.createElement("option");
                    updatedContactOption.value = initialSelection.url;
                    updatedContactOption.text = initialSelection.name;

                    selectElement.add(updatedContactOption);
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
                    onChange: updateDetailSelection,
                });

                selectElement.classList.add("hidden");
                tomSelectInstance.control_input.parentElement.classList.add("tox-textfield");
                if (initialSelection) {
                    tomSelectInstance.options[initialSelection.url] = initialSelection;
                    tomSelectInstance.setValue(initialSelection.url);
                } else {
                    // when initial selection is given, do not focus the input,
                    // in order to avoid an additional click to see the full details selection
                    tomSelectInstance.control_input.focus();
                }
                setSubmitDisableStatus(tomSelectInstance.getValue());
            }, 0);

            return editor.windowManager.open(dialogConfig);
        };

        if (isContactsEnabled) {
            editor.addShortcut("Meta+L", tinymceConfig.getAttribute("data-contact-menu-text"), openDialog);

            editor.ui.registry.addMenuItem("add_contact", {
                text: tinymceConfig.getAttribute("data-contact-menu-text"),
                icon: "contact",
                shortcut: "Meta+L",
                onAction: openDialog,
            });
        }

        editor.ui.registry.addButton("change_contact", {
            text: tinymceConfig.getAttribute("data-contact-change-text"),
            icon: "contact",
            onAction: async () => {
                const contactUrl = getContact().dataset.contactUrl;
                const updatedContact = await getContactRaw(contactUrl);
                const selectedDetails = contactUrl.split("?details=")[1]?.split(",");

                openDialog(null, updatedContact, selectedDetails);
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
            items: isContactsEnabled ? "change_contact remove_contact" : "remove_contact",
        });

        // Ensure <details> are by default open in the editor, when they are not clickable as part of the contact card, but outside
        /* eslint no-param-reassign: ["error", { "props": false }] */
        editor.on("BeforeSetContent", (e) => {
            e.content = e.content.replace("<details>", "<details open>");
        });
        editor.on("PreProcess", (e) => {
            const elements = Array.from(e.node.querySelectorAll('[data-contact-id][contenteditable="false"] details'));
            elements.forEach((node) => {
                node.open = false;
            });
        });

        return {};
    });
})();

/**
 * Renders and submits a contact creation form inline via AJAX.
 *
 * Attached to the root element via `data-js-ajax-contact-form`.
 * Expects the following elements within root:
 *   - `#show-contact-form-button`               — button to load the form, with a `data-url` attribute pointing to the form HTML endpoint
 *   - `#contact-form-widget`                    — container into which the form HTML is injected
 *   - `#related-contact`                        — block that indicates a contact can be linked
 *   - `#related-contact-list`                   — list to which newly created contacts are appended
 *   - `#submit-contact-form-button`             — submit button inside the injected form, with a `data-url` attribute for the POST endpoint
 *   - `#contact-ajax-success-message`           — success message element (hidden by default)
 *   - `#contact-ajax-error-message`             — container for field validation error messages
 *   - `#contact-ajax-unexpected-error-message`  — fallback error message element (hidden by default)
 *
 * On clicking the show-button the form HTML is fetched and injected. On submit
 * the form data is POSTed to `data-url`; on success the new contact is appended
 * to the list and the form is hidden, on failure validation errors are displayed.
 * If `#id_area_of_responsibility` already has a validation error on page load
 * the form is shown immediately.
 *
 * @module ajax-contact-form
 */
import { getCsrfToken } from "../utils/csrf-token";
import { createIconsAt } from "../utils/create-icons";
import { defineFeature } from "../utils/define-feature";

const hideContactFormWidget = (root: HTMLElement) => {
    const widget = root.querySelector("#contact-form-widget") as HTMLElement;
    if (widget) {
        widget.textContent = "";
        root.querySelector("#show-contact-form-button").classList.remove("hidden");
    }
};

const addNewContactToList = (root: HTMLElement, label: string, url: string) => {
    const relatedContactList = root.querySelector("#related-contact-list") as HTMLElement;
    const newContactRow = document.createElement("a");

    newContactRow.href = url;
    newContactRow.innerHTML = `<i icon-name="pencil" class="mr-2"></i> ${label}`;
    newContactRow.classList.add("block", "pt-2", "hover:underline");

    relatedContactList.appendChild(newContactRow);
    createIconsAt(relatedContactList);
};

const showMessage = (root: HTMLElement, data: any) => {
    if (data.success) {
        hideContactFormWidget(root);
        addNewContactToList(root, data.contact_label, data.edit_url);
        const successMessageField = root.querySelector("#contact-ajax-success-message");
        successMessageField.classList.remove("hidden");
    } else if (data.contact_form.length > 0) {
        const errorMessageField = root.querySelector("#contact-ajax-error-message");
        data.contact_form.forEach((error: any) => {
            const node = document.createElement("div");
            node.classList.add("bg-red-100", "border-l-4", "border-red-500", "text-red-700", "px-4", "py-3", "my-1");
            node.innerText = error.text;
            errorMessageField.append(node);
        });
    } else {
        const unexpectedErrorMessageField = root.querySelector("#contact-ajax-unexpected-error-message");
        unexpectedErrorMessageField.classList.remove("hidden");
    }
};

const clearPreviousMessages = (root: HTMLElement) => {
    const successMessageField = root.querySelector("#contact-ajax-success-message");
    successMessageField.classList.add("hidden");

    const errorMessageField = root.querySelector("#contact-ajax-error-message");
    errorMessageField.replaceChildren();

    const unexpectedErrorMessageField = root.querySelector("#contact-ajax-unexpected-error-message");
    unexpectedErrorMessageField.classList.add("hidden");
};

const createContact = async (event: Event, root: HTMLElement) => {
    event.preventDefault();
    const btn = event.target as HTMLInputElement;
    const form = btn.form as HTMLFormElement;
    const formData: FormData = new FormData(form);
    formData.append(btn.name, btn.value);
    if (!form.reportValidity()) {
        return;
    }

    clearPreviousMessages(root);

    const response = await fetch(btn.getAttribute("data-url"), {
        method: "POST",
        headers: {
            "X-CSRFToken": getCsrfToken(),
        },
        body: formData,
    });

    const data = await response.json();
    showMessage(root, data);
};

const renderContactForm = async (root: HTMLElement) => {
    const showContactFormButton = root.querySelector("#show-contact-form-button");
    const submitContactFormButton = root.querySelector("#submit-contact-form-button");
    const contactFormWidget = root.querySelector("#contact-form-widget");
    contactFormWidget.classList.remove("hidden");
    const relatedContactBlock = root.querySelector("#related-contact");
    if (relatedContactBlock) {
        const response = await fetch(showContactFormButton.getAttribute("data-url"));
        contactFormWidget.innerHTML = await response.text();

        submitContactFormButton.addEventListener("click", (event) => {
            event.preventDefault();
            createContact(event, root);
        });
    }
    showContactFormButton.classList.add("hidden");
};

export default defineFeature((root) => {
    root.querySelector("#show-contact-form-button")?.addEventListener("click", (event) => {
        event.preventDefault();
        clearPreviousMessages(root);
        renderContactForm(root);
    });
    if (root.querySelector("#id_area_of_responsibility")?.classList.contains("border-red-500")) {
        root.querySelector("contact-form-widget").classList.remove("hidden");
        root.querySelector("show-contact-form-button").classList.add("hidden");
    }
});

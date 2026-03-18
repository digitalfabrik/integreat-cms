import { getCsrfToken } from "../utils/csrf-token";
import { createIconsAt } from "../utils/create-icons";
import { defineFeature } from "../utils/define-feature";

const hideContactFormWidget = () => {
    const widget = document.getElementById("contact-form-widget") as HTMLElement;
    if (widget) {
        widget.textContent = "";
        document.getElementById("show-contact-form-button").classList.remove("hidden");
    }
};

const addNewContactToList = (label: string, url: string) => {
    const relatedContactList = document.getElementById("related-contact-list");
    const newContactRow = document.createElement("a");

    newContactRow.href = url;
    newContactRow.innerHTML = `<i icon-name="pencil" class="mr-2"></i> ${label}`;
    newContactRow.classList.add("block", "pt-2", "hover:underline");

    relatedContactList.appendChild(newContactRow);
    createIconsAt(relatedContactList);
};

const showMessage = (data: any) => {
    if (data.success) {
        hideContactFormWidget();
        addNewContactToList(data.contact_label, data.edit_url);
        const successMessageField = document.getElementById("contact-ajax-success-message");
        successMessageField.classList.remove("hidden");
    } else if (data.contact_form.length > 0) {
        const errorMessageField = document.getElementById("contact-ajax-error-message");
        data.contact_form.forEach((error: any) => {
            const node = document.createElement("div");
            node.classList.add("bg-red-100", "border-l-4", "border-red-500", "text-red-700", "px-4", "py-3", "my-1");
            node.innerText = error.text;
            errorMessageField.append(node);
        });
    } else {
        const unexpectedErrorMessageField = document.getElementById("contact-ajax-unexpected-error-message");
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
    showMessage(data);
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

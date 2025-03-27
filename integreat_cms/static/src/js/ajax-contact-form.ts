import { getCsrfToken } from "./utils/csrf-token";
import { createIconsAt } from "./utils/create-icons";

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
    const timeoutDuration = 10000;
    if (data.success) {
        hideContactFormWidget();
        addNewContactToList(data.contact_label, data.edit_url);
        const successMessageField = document.getElementById("contact-ajax-success-message");
        successMessageField.classList.remove("hidden");
        setTimeout(() => {
            successMessageField.classList.add("hidden");
        }, timeoutDuration);
    } else {
        const errorMessageField = document.getElementById("contact-ajax-error-message");
        errorMessageField.classList.remove("hidden");
        setTimeout(() => {
            errorMessageField.classList.add("hidden");
        }, timeoutDuration);
    }
};

const createContact = async (event: Event) => {
    event.preventDefault();
    const btn = event.target as HTMLInputElement;
    const form = btn.form as HTMLFormElement;
    const formData: FormData = new FormData(form);
    formData.append(btn.name, btn.value);
    if (!form.reportValidity()) {
        return;
    }

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

const renderContactForm = async () => {
    document.getElementById("contact-form-widget").classList.remove("hidden");
    const relatedContactBlock = document.getElementById("related-contact");
    if (relatedContactBlock) {
        const response = await fetch(document.getElementById("show-contact-form-button").getAttribute("data-url"));
        document.getElementById("contact-form-widget").innerHTML = await response.text();

        document.getElementById("submit-contact-form-button").addEventListener("click", (event) => {
            event.preventDefault();
            createContact(event);
        });
    }
    document.getElementById("show-contact-form-button").classList.add("hidden");
};

window.addEventListener("load", () => {
    document.getElementById("show-contact-form-button")?.addEventListener("click", (event) => {
        event.preventDefault();
        renderContactForm();
    });

    document.querySelectorAll("[contact-poi-box]").forEach((el) => {
        el.addEventListener("submit", async (event) => {
            event.preventDefault();
            const btn = event.target as HTMLInputElement;
            const form = btn.form as HTMLFormElement;
            const formData: FormData = new FormData(form);
            formData.append(btn.name, btn.value);
            if (!form.reportValidity()) {
                return;
            }
            const response = await fetch(btn.getAttribute("data-url"), {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                },
                body: formData,
            });
            const messages = await response.json();
            showMessage(messages);
        });
    });
});

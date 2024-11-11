import { getCsrfToken } from "./utils/csrf-token";

const showMessage = (response: any) => {
    const timeoutDuration = 10000;
    if (response.success) {
        const successMessageField = document.getElementById("poi-ajax-success-message");
        successMessageField.classList.remove("hidden");
        setTimeout(() => {
            successMessageField.classList.add("hidden");
        }, timeoutDuration);
    } else {
        const errorMessageField = document.getElementById("poi-ajax-error-message");
        errorMessageField.classList.remove("hidden");
        setTimeout(() => {
            errorMessageField.classList.add("hidden");
        }, timeoutDuration);
    }
};

window.addEventListener("load", () => {
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
            // Handle messages
            const messages = await response.json();
            console.debug(messages);
            showMessage(messages);
        });
    });
});
